from apps.mix.models import MixProject, MixClip
from django.db.models import F


def create_mix_project(user, title: str, description: str = None, bpm: int = None) -> MixProject:
    return MixProject.objects.create(
        user=user, title=title, description=description, bpm=bpm, status='draft',
    )


def add_clip(mix_project: MixProject, *, position: int,
             song_id: str = None, stem_file_id: str = None,
             start_time_ms: int = 0, end_time_ms: int,
             fade_in_ms: int = 0, fade_out_ms: int = 0,
             volume: float = 1.0) -> MixClip:
    """Agrega un clip al mix. Valida fuente y rango de tiempo."""
    if not any([song_id, stem_file_id]):
        raise ValueError("Se requiere song_id o stem_file_id.")

    if end_time_ms <= start_time_ms:
        raise ValueError("end_time_ms debe ser mayor que start_time_ms.")

    # Desplazar clips existentes para dejar espacio en la posición pedida
    MixClip.objects.filter(
        mix_project=mix_project, position__gte=position
    ).update(position=F('position') + 1)

    return MixClip.objects.create(
        mix_project=mix_project,
        song_id=song_id,
        stem_file_id=stem_file_id,
        position=position,
        start_time_ms=start_time_ms,
        end_time_ms=end_time_ms,
        fade_in_ms=fade_in_ms,
        fade_out_ms=fade_out_ms,
        volume=volume,
    )


def reorder_clips(mix_project: MixProject, clip_order: list) -> None:
    """Reordena los clips. clip_order: lista de UUIDs (str) en el nuevo orden."""
    for new_position, clip_id in enumerate(clip_order):
        MixClip.objects.filter(id=clip_id, mix_project=mix_project).update(
            position=new_position
        )


def remove_clip(clip_id: str, user) -> None:
    """Elimina un clip verificando que el mix sea del usuario."""
    clip = MixClip.objects.select_related('mix_project').get(id=clip_id)
    if str(clip.mix_project.user_id) != str(user.id):
        raise PermissionError("No tenés permiso para eliminar este clip.")
    clip.delete()
