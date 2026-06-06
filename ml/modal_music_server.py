import base64
from typing import List
import uuid
import modal
import os
import boto3

from pydantic import BaseModel
import requests

from prompts import LYRICS_GENERATOR_PROMPT, PROMPT_GENERATOR_PROMPT

app = modal.App("gm-music-server")

image = (
    modal.Image.debian_slim()
    .apt_install("git", "ffmpeg")
    .run_commands(["git clone https://github.com/ace-step/ACE-Step.git /tmp/ACE-Step", "cd /tmp/ACE-Step && pip install ."])
    .pip_install(
        "demucs>=4.0.0",
        "transformers==4.50.0",
        "accelerate==1.6.0",
        "diffusers==0.33.0",
        "boto3",
        "pydantic",
        "requests",
        "torch",
        "torchaudio",
        "torchcodec"
    )
    .env({"HF_HOME": "/.cache/huggingface"})
    .add_local_python_source("prompts")
)

model_volume = modal.Volume.from_name("ace-step-models", create_if_missing=True)
hf_volume = modal.Volume.from_name("qwen-hf-cache", create_if_missing=True)

music_gen_secrets = modal.Secret.from_name("music-gen-secret")


class AudioGenerationBase(BaseModel):
    audio_duration: float = 180.0
    seed: int = -1
    guidance_scale: float = 15.0
    infer_step: int = 60
    instrumental: bool = False


class GenerateFromDescriptionRequest(AudioGenerationBase):
    full_described_song: str


class GenerateWithCustomLyricsRequest(AudioGenerationBase):
    prompt: str
    lyrics: str


class GenerateWithDescribedLyricsRequest(AudioGenerationBase):
    prompt: str
    described_lyrics: str


class GenerateMusicResponseS3(BaseModel):
    s3_key: str
    cover_image_s3_key: str
    categories: List[str]


# ─── CAMBIO 1: scaledown_window aumentado a 300s (5 min) ───────────────────────
# Con 15s, la GPU se apagaba y re-encendía constantemente entre peticiones.
# Cada cold start de A100 tarda ~3-5 min y cuesta créditos. Con 300s, si llegan
# 2 requests en menos de 5 minutos, la GPU ya está caliente y no hay cold start.
# Ajustá este valor según tu volumen de tráfico real.
@app.cls(
    image=image,
    gpu="A100",
    volumes={"/models": model_volume, "/.cache/huggingface": hf_volume},
    secrets=[music_gen_secrets],
    scaledown_window=300,
)
class MusicGenServer:

    @modal.enter()
    def load_model(self):
        import torch
        from acestep.pipeline_ace_step import ACEStepPipeline
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from diffusers import AutoPipelineForText2Image

        # ── Music Generation Model ──────────────────────────────────────────────
        # CAMBIO 2: cpu_offload=True
        # ACE-Step es el modelo más pesado. Con cpu_offload=True, las capas que
        # no se usan en ese momento se mueven a RAM, liberando VRAM para Qwen y SDXL.
        # Si tu A100 tiene 80GB podés volver a False, pero con 40GB es necesario.
        self.music_model = ACEStepPipeline(
            checkpoint_dir="/models",
            dtype="bfloat16",
            torch_compile=False,
            cpu_offload=True,   # <-- CAMBIO: False → True
            overlapped_decode=False
        )

        # ── LLM (Qwen) ─────────────────────────────────────────────────────────
        model_id = "Qwen/Qwen2-7B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype="auto",
            device_map="auto",
            cache_dir="/.cache/huggingface"
        )

        # ── Stable Diffusion (thumbnails) ───────────────────────────────────────
        self.image_pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=torch.float16,
            variant="fp16",
            cache_dir="/.cache/huggingface"
        )
        self.image_pipe.to("cuda")

    # ─── CAMBIO 3: helper centralizado de limpieza de memoria ──────────────────
    # En el código original, el gc.collect()+empty_cache() solo estaba en
    # generate_with_described_lyrics. Ahora se llama desde todos los flujos que
    # usan Qwen antes de pasarle el trabajo a ACE-Step.
    def _flush_llm_cache(self):
        import torch  # ← acá adentro
        import gc 
        """Libera la VRAM que ocupó Qwen antes de correr ACE-Step o SDXL."""
        gc.collect()
        torch.cuda.empty_cache()

    def prompt_qwen(self, question: str):
        messages = [{"role": "user", "content": question}]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.llm_model.device)

        generated_ids = self.llm_model.generate(
            model_inputs.input_ids,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

    def generate_prompt(self, description: str):
        full_prompt = PROMPT_GENERATOR_PROMPT.format(user_prompt=description)
        return self.prompt_qwen(full_prompt)

    def generate_lyrics(self, description: str, duration: float):
        full_prompt = LYRICS_GENERATOR_PROMPT.format(description=description, duration=duration)
        return self.prompt_qwen(full_prompt)

    def generate_categories(self, description: str) -> List[str]:
        prompt = (
            f"Based on the following music description, list 3-5 relevant genres or categories "
            f"as a comma-separated list. For example: Pop, Electronic, Sad, 80s. "
            f"Description: '{description}'"
        )
        response_text = self.prompt_qwen(prompt)
        return [cat.strip() for cat in response_text.split(",") if cat.strip()]

    def generate_and_upload_to_s3(
        self,
        prompt: str,
        lyrics: str,
        instrumental: bool,
        audio_duration: float,
        infer_step: int,
        guidance_scale: float,
        seed: int,
        description_for_categorization: str,
    ) -> GenerateMusicResponseS3:
        final_lyrics = "[instrumental]" if instrumental else lyrics
        print(f"Prompt: {prompt}")
        print(f"Lyrics: {final_lyrics}")

        s3_client = boto3.client("s3")
        bucket_name = os.environ["S3_BUCKET_NAME"]
        output_dir = "/tmp/outputs"
        os.makedirs(output_dir, exist_ok=True)

        # ── 1. Generar audio con ACE-Step ───────────────────────────────────────
        output_path = os.path.join(output_dir, f"{uuid.uuid4()}.wav")
        self.music_model(
            prompt=prompt,
            lyrics=final_lyrics,
            audio_duration=audio_duration,
            infer_step=infer_step,
            guidance_scale=guidance_scale,
            save_path=output_path,
            manual_seeds=str(seed),
        )
        audio_s3_key = f"{uuid.uuid4()}.wav"
        s3_client.upload_file(output_path, bucket_name, audio_s3_key)
        os.remove(output_path)

        # ── 2. Generar thumbnail con SDXL ───────────────────────────────────────
        thumbnail_prompt = f"{prompt}, album cover art"
        image = self.image_pipe(
            prompt=thumbnail_prompt, num_inference_steps=2, guidance_scale=0.0
        ).images[0]
        image_output_path = os.path.join(output_dir, f"{uuid.uuid4()}.png")
        image.save(image_output_path)
        image_s3_key = f"{uuid.uuid4()}.png"
        s3_client.upload_file(image_output_path, bucket_name, image_s3_key)
        os.remove(image_output_path)

        # ── 3. Generar categorías con Qwen ──────────────────────────────────────
        # CAMBIO 4: las categorías se generan AL FINAL, después de ACE-Step y SDXL.
        # Antes, en generate_and_upload_to_s3 se llamaba a generate_categories()
        # al final igual, pero los endpoints que usan Qwen para letras/prompt no
        # llamaban a _flush_llm_cache() antes de entrar acá. Ahora sí (ver abajo).
        categories = self.generate_categories(description_for_categorization)

        return GenerateMusicResponseS3(
            s3_key=audio_s3_key,
            cover_image_s3_key=image_s3_key,
            categories=categories,
        )

    # ─── CAMBIO 5: endpoint `generate` de prueba ELIMINADO ─────────────────────
    # El endpoint hardcodeado /generate existía solo para testing pero estaba
    # expuesto en producción. Cualquier llamada accidental (o un bot que lo
    # descubra) consumía una generación completa de 180s en A100. Eliminado.

    @modal.fastapi_endpoint(method="POST")
    def generate_from_description(self, request: GenerateFromDescriptionRequest) -> GenerateMusicResponseS3:
        prompt = self.generate_prompt(request.full_described_song)
        lyrics = ""
        if not request.instrumental:
            lyrics = self.generate_lyrics(request.full_described_song, request.audio_duration)

        # CAMBIO 3 aplicado: limpiar VRAM de Qwen antes de correr ACE-Step
        self._flush_llm_cache()

        return self.generate_and_upload_to_s3(
            prompt=prompt,
            lyrics=lyrics,
            description_for_categorization=request.full_described_song,
            **request.model_dump(exclude={"full_described_song"}),
        )

    @modal.fastapi_endpoint(method="POST")
    def generate_with_lyrics(self, request: GenerateWithCustomLyricsRequest) -> GenerateMusicResponseS3:
        # Este endpoint no usa Qwen para letras, pero sí para categorías dentro
        # de generate_and_upload_to_s3. No hay Qwen antes, así que no hace falta
        # flush aquí — pero lo dejamos por consistencia ante futuros cambios.
        return self.generate_and_upload_to_s3(
            prompt=request.prompt,
            lyrics=request.lyrics,
            description_for_categorization=request.prompt,
            **request.model_dump(exclude={"prompt", "lyrics"}),
        )

    @modal.fastapi_endpoint(method="POST")
    def generate_with_described_lyrics(self, request: GenerateWithDescribedLyricsRequest) -> GenerateMusicResponseS3:
        lyrics = ""
        if not request.instrumental:
            lyrics = self.generate_lyrics(request.described_lyrics, request.audio_duration)

        # CAMBIO 3 aplicado: mismo patrón que generate_from_description
        self._flush_llm_cache()

        return self.generate_and_upload_to_s3(
            prompt=request.prompt,
            lyrics=lyrics,
            description_for_categorization=request.prompt,
            **request.model_dump(exclude={"described_lyrics", "prompt"}),
        )

    @modal.fastapi_endpoint(method="GET")
    def health(self):
        return {"status": "ok", "model": "ace-step"}

    @modal.fastapi_endpoint(method="POST")
    def separate_stems(self, request: dict):
        """
        Separa un archivo de audio en pistas con Demucs.
        Input:  { s3_key: str, stems: ['vocals', 'no_vocals'] }
        Output: { stems: { vocals: s3_key, no_vocals: s3_key, ... } }
        """
        import demucs.separate
        import boto3, tempfile, os
        from pathlib import Path

        s3 = boto3.client('s3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
        )

        # Descargar el audio de S3 a un archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            s3.download_fileobj(os.environ.get('AWS_STORAGE_BUCKET_NAME', 'gm-storage'), request['s3_key'], tmp)
            input_path = tmp.name

        # Separar con Demucs (modo two-stems: vocals vs no_vocals)
        output_dir = tempfile.mkdtemp()
        demucs.separate.main([
            '--two-stems', 'vocals',
            '--out', output_dir,
            input_path
        ])

        # Subir los stems resultantes a S3
        result = {}
        base_name = Path(input_path).stem
        model_dir = Path(output_dir) / 'htdemucs' / base_name

        for stem_type in ['vocals', 'no_vocals']:
            stem_file = model_dir / f'{stem_type}.wav'
            if stem_file.exists():
                s3_key = f"stems/{request['s3_key'].split('/')[-1]}/{stem_type}.wav"
                s3.upload_file(str(stem_file), os.environ.get('AWS_STORAGE_BUCKET_NAME', 'gm-storage'), s3_key)
                result[stem_type] = s3_key

        return {'stems': result}



@app.local_entrypoint()
def main():
    server = MusicGenServer()
    endpoint_url = server.generate_with_described_lyrics.get_web_url()

    request_data = GenerateWithDescribedLyricsRequest(
        prompt="rave, funk, 140BPM, disco",
        described_lyrics="lyrics about water bottles",
        guidance_scale=15,
    )

    response = requests.post(endpoint_url, json=request_data.model_dump())
    response.raise_for_status()
    result = GenerateMusicResponseS3(**response.json())
    print(f"Success: {result.s3_key} {result.cover_image_s3_key} {result.categories}")