# Guía de Pruebas End-to-End — Generador Musical SaaS
> Versión: producción en Railway
> Fecha de uso prevista: cuando la base esté en Railway y el seeder ejecutado
> Grupo: 5 personas — cliente1 a cliente5
> **Leer completo antes de empezar. El orden importa.**

---

## Índice

1. [Preparación pre-prueba](#1-preparación-pre-prueba)
2. [Credenciales y cuentas](#2-credenciales-y-cuentas)
3. [Estrategia Modal (límite de 2 canciones por cuenta)](#3-estrategia-modal)
4. [Fase 1 — Autenticación](#4-fase-1--autenticación)
5. [Fase 2 — Generación de canciones (30 canciones, asignación exacta)](#5-fase-2--generación-de-canciones)
6. [Fase 3 — Biblioteca personal](#6-fase-3--biblioteca-personal)
7. [Fase 4 — Publicar en comunidad](#7-fase-4--publicar-en-comunidad)
8. [Fase 5 — Comunidad (feed, likes, plays)](#8-fase-5--comunidad)
9. [Fase 6 — Stems / Karaoke](#9-fase-6--stems--karaoke)
10. [Fase 7 — Playlists manuales y automáticas](#10-fase-7--playlists)
11. [Fase 8 — Recomendaciones "Para ti"](#11-fase-8--recomendaciones)
12. [Fase 9 — Mix DJ](#12-fase-9--mix-dj)
13. [Fase 10 — Panel de administración](#13-fase-10--panel-de-administración)
14. [Checklist final de verificación](#14-checklist-final)

---

## 1. Preparación pre-prueba

### 1.1 Deploy en Railway
Ya esta (Solo la base)

### 1.3 Obtener URLs de Modal

Después del deploy en Modal (`modal deploy ml/modal_music_server.py`), copiar cada URL y pegarla en las variables de Railway. Las URLs tienen el formato:
```
https://<tu-org>--gm-music-server-musicgenserver-<endpoint>.modal.run
```

---

## 2. Credenciales y cuentas

| Persona | Email Django | Contraseña | Asignación de gustos |
|---------|-------------|------------|---------------------|
| Persona 1 | cliente1@gmail.com | cliente1234 | Lofi · Jazz · Chill · Melancólico |
| Persona 2 | cliente2@gmail.com | cliente1234 | Lofi · Chill · Pop · Triste |
| Persona 3 | cliente3@gmail.com | cliente1234 | Reggaeton · Pop · Energético · Feliz |
| Persona 4 | cliente4@gmail.com | cliente1234 | Reggaeton · Bachata · Urbano · Romántico |
| Persona 5 | cliente5@gmail.com | cliente1234 | Rock · Kpop · Ranchera · Cumbia · Diverso |
| **Admin** | admin@musicgen.com | admin1234 | Panel de administración |

> **Por qué estos gustos:** Personas 1 y 2 comparten lofi/chill → el sistema de recomendaciones debe sugerirles canciones del otro. Personas 3 y 4 comparten reggaeton/energético → también deben aparecer como usuarios similares. Persona 5 es diversa para verificar que no confunda los perfiles.

---

## 3. Estrategia Modal
cd gm-backend/ml
pip install modal
modal setup                  # autenticarse con la cuenta de Modal (copiar en MODAL_KEY y MODAL_SECRET)
modal deploy modal_music_server.py      #copiar URL finales en .env


EN MODAL  crear secret
#ir a https://modal.com/secrets/<Username>/main
name:
music-gen-secret

variables:
S3_BUCKET_NAME=*********** (misma que AWS_STORAGE_BUCKET_NAME)
AWS_ACCESS_KEY_ID=***********
AWS_SECRET_ACCESS_KEY=***********
AWS_S3_REGION_NAME=***********

leer guia docs/setup_redis_celery
#wsl sudo service redis-server start  --inicar redis

#salir de modal para iniciar sesion con otras cuentas
modal token new
---

## 4. Fase 1 — Autenticación

**Todas las personas hacen esto primero, cada una en su computadora.**

### 4.1 Registro (opcional — ya están en el seeder)

Las cuentas ya existen gracias al seeder. **No hay que registrarse.** Ir directo al login.

### 4.2 Login

1. Ir a `https://localhost/login`
2. Email: `cliente1@gmail.com` (cada uno el suyo)
3. Password: `cliente1234`
4. Clic en **Iniciar sesión**
5. Pagar un plan con stripe
  Tarjeta Visa test (pago exitoso) : 4242 4242 4242 4242
  Tarjeta que falla               : 4000 0000 0000 0002
  CVC cualquiera · Fecha futura cualquiera · ZIP 00000

**Resultado esperado:** Redirige a `/` (inicio). En el sidebar aparece la navegación completa. En el header superior derecho aparece el balance de créditos.

### 4.3 Verificar header

En la esquina superior derecha deben ver:
- Ícono de moneda con el número `20` y texto "créditos"
- Ícono de campana (notificaciones)
- Su nombre y email

---

## 5. Fase 2 — Generación de canciones

> **IMPORTANTE:** Esta es la fase más crítica. Cada persona genera exactamente 6 canciones en el orden indicado. No saltear ni cambiar las descripciones — están diseñadas para que las recomendaciones funcionen correctamente al final.
>
> Ir a **Crear canción** en el sidebar. El crédito se descuenta cuando la canción se pone en cola. Una generación tarda entre 3 y 8 minutos dependiendo del cold start del servidor Modal.

### Modos de generación — cómo funcionan

| Pestaña en UI | Lo que hace |
|--------------|-------------|
| **Descripción** | Describe el estilo en texto libre. La IA infiere prompt y letra automáticamente. |
| **Letra automática** | Vos escribís el estilo/prompt + describís de qué trata la letra. La IA escribe la letra. |
| **Letra exacta** | Vos escribís el prompt de estilo + la letra completa tal cual debe quedar. |

### Cómo usar los tags de estilo (nuevo)

Debajo del campo de modo aparece un selector de tags con tres grupos: **Género**, **Mood** y **Tempo**.

- **Modo Descripción:** clic en los tags ANTES de escribir la descripción. Los tags seleccionados se anteponen automáticamente a la descripción al enviar (ej: `lofi, chill, slow. [tu descripción]`).
- **Modo Letra Exacta / Letra Autogenerada:** los tags se combinan con el campo "Estilo musical". Podés clickear los tags Y también escribir en el campo, o solo hacer clic en los tags si preferís no escribir el prompt manualmente.

Al terminar de seleccionar tags, los verás listados en una fila de chips morados debajo del selector — confirmación visual de lo que se va a enviar.

> **Los tags se resetean automáticamente al cambiar de modo o al hacer "Nueva canción".**

---

### NATALY — cliente1@gmail.com (Lofi · Jazz · Chill)

#### Canción 1 (modo: Descripción)
- **Pestaña:** Descripción
- **Título:** `Lluvia de Medianoche`
- **Tags a clickear:** `lofi` · `chill` · `melancholic` · `slow`
- **Descripción (copiar exacto):**
  ```
  Una canción lofi instrumental, tranquila y melancólica, perfecta para estudiar de noche. Sin letra, solo piano suave con lluvia de fondo, beat relajado a 75bpm. Quiero que transmita soledad cálida, esa sensación de estar seguro en casa mientras llueve afuera.
  ```
- **Duración:** 1 min
- **Instrumental:** activar el toggle (sin letra)
- Clic **Generar canción**

#### Canción 2 (modo: Descripción)
- **Pestaña:** Descripción
- **Título:** `Café con Jazz`
- **Tags a clickear:** `jazz` · `melancholic` · `nostalgic` · `medium`
- **Descripción:**
  ```
  Balada jazz nocturna con saxofón, piano y contrabajo. Letra melancólica sobre recordar a alguien que ya no está, con un tono nostálgico pero sereno. Tempo moderado 90bpm. Quiero que suene como algo que sonarías en un bar de jazz a las 2am.
  ```
- **Duración:** 1 min
- **Instrumental:** desactivado

#### Canción 3 (modo: Letra automática)
- **Pestaña:** Letra automática
- **Título:** `3AM en la Biblioteca`
- **Tags a clickear:** `lofi` · `chill` · `sad` · `medium`
- **Prompt de estilo** (dejar vacío — los tags ya lo completan):
  ```
  piano, 80bpm, acoustic
  ```
- **Descripción de letra:**
  ```
  Letra sobre un estudiante que estudia hasta las 3am, cansado pero motivado, con pensamientos dispersos, echando de menos su cama, humor melancólico pero esperanzador
  ```
- **Duración:** 1 min

#### Canción 4 (modo: Letra automática)
- **Pestaña:** Letra automática
- **Título:** `Reencuentro`
- **Tags a clickear:** `jazz` · `nostalgic` · `medium`
- **Prompt de estilo:**
  ```
  piano, acoustic guitar, soft percussion, 85bpm
  ```
- **Descripción de letra:**
  ```
  Dos viejos amigos que se reencuentran después de años sin verse. Conversación agridulce, recuerdos de juventud, la vida que siguió para cada uno. Tono nostálgico y cálido
  ```
- **Duración:** 1 min

#### Canción 5 (modo: Letra exacta)
- **Pestaña:** Letra exacta
- **Título:** `Otoño en mis Pasos`
- **Tags a clickear:** `sad` · `melancholic` · `slow`
- **Prompt de estilo:**
  ```
  acoustic folk, guitar fingerpicking, 70bpm
  ```
- **Letra (copiar exacto):**
  ```
  Las hojas caen como recuerdos
  que el viento se lleva sin avisar
  Caminé por donde solíamos ir
  y el silencio me habló de ti

  Ya no hay nada que decir
  solo el eco de lo que fue
  El otoño vive en mis pasos
  y en todo lo que ya no es
  ```
- **Duración:** 1 min

#### Canción 6 (modo: Letra exacta)
- **Pestaña:** Letra exacta
- **Título:** `Lo Que Queda`
- **Tags a clickear:** `lofi` · `nostalgic` · `chill`
- **Prompt de estilo:**
  ```
  boom bap, warm, vinyl scratch, 85bpm
  ```
- **Letra:**
  ```
  Guardo fotos que ya no miro
  conversaciones sin responder
  El tiempo es raro, te lo juro
  todo cambia sin querer

  Pero algo queda en el fondo
  algo que no puedo nombrar
  Un sabor entre los sueños
  que no me deja olvidar
  ```
- **Duración:** 1 min

---

### NICOL 2 — cliente2@gmail.com (Lofi · Pop · Triste)

#### Canción 1 (modo: Descripción)
- **Título:** `Noches sin Señal`
- **Tags a clickear:** `lofi` · `chill` · `sad` · `slow`
- **Descripción:**
  ```
  Canción lofi chill sobre el insomnio y revisar el celular a las 4am esperando un mensaje que no llega. Piano con textura de vinilo, beat suave, nada de batería fuerte, ambiente tranquilo y un poco triste. 80bpm, con letra.
  ```
- **Duración:** 1 min

#### Canción 2 (modo: Descripción)
- **Título:** `Domingo Gris`
- **Tags a clickear:** `pop` · `sad` · `melancholic` · `medium`
- **Descripción:**
  ```
  Pop melancólico de domingo por la tarde. Esa sensación de que la semana ya terminó y la nueva te da pereza. Guitarra acústica, voz suave, letra sobre el ciclo de la rutina y el deseo de escapar. Tempo moderado 95bpm.
  ```
- **Duración:** 1 min

#### Canción 3 (modo: Letra automática)
- **Título:** `Señales de Humo`
- **Tags a clickear:** `lofi` · `chill` · `sad` · `nostalgic`
- **Prompt de estilo:**
  ```
  guitar, piano, 78bpm
  ```
- **Descripción de letra:**
  ```
  Letra sobre alguien que intenta comunicarse con otra persona que se alejó, usando metáforas de señales de humo, cartas no enviadas, mensajes en el viento. Sensación de distancia inevitable.
  ```
- **Duración:** 1 min

#### Canción 4 (modo: Letra automática)
- **Título:** `Último Verano`
- **Tags a clickear:** `pop` · `romantic` · `slow`
- **Prompt de estilo:**
  ```
  piano ballad, 85bpm, emotional
  ```
- **Descripción de letra:**
  ```
  El último verano antes de que todo cambiara. Una relación que terminó pero dejó recuerdos bonitos. Tono agridulce, ni completamente triste ni completamente feliz, sino esa paz de haber amado bien.
  ```
- **Duración:** 1 min

#### Canción 5 (modo: Letra exacta)
- **Título:** `El Cuarto de al Lado`
- **Tags a clickear:** `sad` · `slow`
- **Prompt de estilo:**
  ```
  acoustic guitar, soft vocal, 68bpm, folk
  ```
- **Letra:**
  ```
  Tu risa atravesaba la pared
  ahora solo escucho el silencio crecer
  Dejaste libros en el estante
  y yo los leo como si fueran mensajes

  El cuarto de al lado ya no es tuyo
  pero igual te busco en cada rincón
  ```
- **Duración:** 1 min

#### Canción 6 (modo: Letra exacta)
- **Título:** `Fade Out`
- **Tags a clickear:** `lofi` · `chill` · `nostalgic` · `slow`
- **Prompt de estilo:**
  ```
  piano, 72bpm, atmospheric
  ```
- **Letra:**
  ```
  Todo se va apagando igual
  como señal de radio al amanecer
  Me quedé mirando el techo
  mientras el mundo siguió su vez

  Nada termina con un golpe
  todo se disuelve despacito
  Como luz que baja el volumen
  hasta quedar en silencio bonito
  ```
- **Duración:** 1 min

---

### JAEL 3 — cliente3@gmail.com (Reggaeton · Pop · Energético)

#### Canción 1 (modo: Descripción)
- **Título:** `La Calle Pide Más`
- **Tags a clickear:** `reggaeton` · `energetic` · `happy` · `fast`
- **Descripción:**
  ```
  Reggaeton puro y duro, beat urbano, 100bpm, perreo pesado, letra sobre el éxito y la calle que pide más de vos. Estilo flow directo, con gancho repetitivo pegajoso. Que suene como los temas que suenan en cualquier fiesta de verano.
  ```
- **Duración:** 1 min

#### Canción 2 (modo: Descripción)
- **Título:** `Noche de Fiesta`
- **Tags a clickear:** `pop` · `happy` · `energetic` · `fast`
- **Descripción:**
  ```
  Pop dance súper pegajoso, perfecto para empezar una fiesta. Beat electrónico con guitarra, letra sobre salir de noche, bailar sin preocupaciones, disfrutar el momento. 120bpm, energía alta, feliz, que te haga mover el pie solo de escucharlo.
  ```
- **Duración:** 1 min

#### Canción 3 (modo: Letra automática)
- **Título:** `El Ritmo No Miente`
- **Tags a clickear:** `reggaeton` · `energetic` · `fast`
- **Prompt de estilo:**
  ```
  urban, latin, 98bpm, bass heavy, trap beat
  ```
- **Descripción de letra:**
  ```
  Letra sobre alguien que sube desde la nada gracias al talento y el esfuerzo, referencia al barrio, al sacrificio, al éxito que llega cuando no te rindes. Actitud desafiante pero sin odio.
  ```
- **Duración:** 1 min

#### Canción 4 (modo: Letra automática)
- **Título:** `Baila Conmigo`
- **Tags a clickear:** `pop` · `happy`
- **Prompt de estilo:**
  ```
  dance, latin, 115bpm, upbeat, electronic
  ```
- **Descripción de letra:**
  ```
  Invitación a bailar en una fiesta, letra juguetona y coqueta, sin complicaciones, sobre la conexión que se siente cuando bailás con alguien que te gusta.
  ```
- **Duración:** 1 min

#### Canción 5 (modo: Letra exacta)
- **Título:** `Del Barrio Pa' Arriba`
- **Tags a clickear:** `reggaeton` · `energetic` · `fast`
- **Prompt de estilo:**
  ```
  urban, 96bpm, dembow, latin
  ```
- **Letra:**
  ```
  Salí del barrio sin mirar pa' atrás
  con el flow en la sangre y ganas de más
  Me dijeron que no iba a llegar
  ahora me escuchan en cada lugar

  Del barrio pa' arriba eso es lo que hay
  el esfuerzo no se negocia ni se da
  ```
- **Duración:** 1 min

#### Canción 6 (modo: Letra exacta)
- **Título:** `Esta Noche Gana el Amor`
- **Tags a clickear:** `pop` · `happy`
- **Prompt de estilo:**
  ```
  dance, 110bpm, synth, electric guitar, upbeat
  ```
- **Letra:**
  ```
  Esta noche no hay reglas que seguir
  el corazón sabe bien a dónde ir
  Soltamos todo lo que nos pesa
  y la pista de baile es nuestra mesa

  Esta noche gana el amor
  no hay razón para tener temor
  Solo quiero verte sonreír
  y bailar hasta el amanecer
  ```
- **Duración:** 1 min

---

### JOB 4 — cliente4@gmail.com (Reggaeton · Bachata · Romántico)

#### Canción 1 (modo: Descripción)
- **Título:** `Tu Nombre en el Beat`
- **Tags a clickear:** `reggaeton` · `romantic` · `slow`
- **Descripción:**
  ```
  Reggaeton romántico, 92bpm, ese estilo perreo lento con letra de amor, cuando el reggaeton se mezcla con una balada urbana. Que transmita atracción, tensión entre dos personas, noche de verano, sobre el filo entre la amistad y el amor.
  ```
- **Duración:** 1 min

#### Canción 2 (modo: Descripción)
- **Título:** `Bachata en el Alma`
- **Tags a clickear:** `bachata` · `romantic` · `slow`
- **Descripción:**
  ```
  Bachata clásica con guitarra típica dominicana, percusión bongó, letra sobre amor perdido y el deseo de volver. Voz con sentimiento, muy romántico y emotivo. 110bpm, estilo Romeo Santos pero con sabor más tradicional.
  ```
- **Duración:** 1 min

#### Canción 3 (modo: Letra automática)
- **Título:** `Pegados al Ritmo`
- **Tags a clickear:** `reggaeton` · `romantic`
- **Prompt de estilo:**
  ```
  urban, 95bpm, dembow, sensual
  ```
- **Descripción de letra:**
  ```
  Dos personas en una fiesta que se encuentran por primera vez bailando, todo pasa a través del baile, la conexión es física pero también emocional. Letra coqueta y directa.
  ```
- **Duración:** 1 min

#### Canción 4 (modo: Letra automática)
- **Título:** `Lo Que Promete la Bachata`
- **Tags a clickear:** `bachata` · `romantic` · `slow`
- **Prompt de estilo:**
  ```
  latin, 105bpm, guitar, bongo
  ```
- **Descripción de letra:**
  ```
  Promesas de amor que se hacen en la pista de baile, cuando el abrazo durante la bachata dice más que mil palabras. La vulnerabilidad de dejarse llevar por el ritmo y por alguien.
  ```
- **Duración:** 1 min

#### Canción 5 (modo: Letra exacta)
- **Título:** `Veneno Dulce`
- **Tags a clickear:** `reggaeton` · `romantic`
- **Prompt de estilo:**
  ```
  sensual, 90bpm, urban, bass, smooth
  ```
- **Letra:**
  ```
  Tus ojos son veneno dulce
  que quiero seguir probando
  Me pierdo en tu sonrisa
  y ya no voy a estar buscando

  Quedémonos aquí callados
  que el silencio habla por nós
  Un reggaeton bien lento
  y el mundo somos tú y yo
  ```
- **Duración:** 1 min

#### Canción 6 (modo: Letra exacta)
- **Título:** `Contigo Hasta el Final`
- **Tags a clickear:** `bachata` · `romantic` · `slow`
- **Prompt de estilo:**
  ```
  108bpm, guitar, passionate, latin
  ```
- **Letra:**
  ```
  No me importa el tiempo que pase
  ni los mares que haya que cruzar
  Donde vayas yo voy a seguirte
  contigo quiero quedarme al final

  Esta bachata que suena esta noche
  me recuerda por qué te elegí
  Porque bailar contigo es como respirar
  no puedo imaginarme sin ti
  ```
- **Duración:** 1 min

---

### BRANDON 5 — cliente5@gmail.com (Rock · Kpop · Ranchera · Cumbia · Diverso)

#### Canción 1 (modo: Descripción)
- **Título:** `Distorsión`
- **Tags a clickear:** `rock` · `angry` · `dark` · `fast`
- **Descripción:**
  ```
  Rock alternativo, guitarras distorsionadas, batería potente, letra sobre frustración y no encajar en el mundo, esa rabia joven que no sabe a dónde ir. 140bpm, estilo indie rock con influencias de años 90, sin filtros.
  ```
- **Duración:** 1 min

#### Canción 2 (modo: Descripción)
- **Título:** `Idol Vibes`
- **Tags a clickear:** `kpop` · `energetic` · `happy` · `fast`
- **Descripción:**
  ```
  Kpop puro, muy producido, synths brillantes, coro épico, beat 128bpm, letra en español con estructura de idol: verso introductorio, pre-coro que sube, coro explosivo. Energía de performance, muy visual, estilo BTS o Stray Kids pero cantado en español.
  ```
- **Duración:** 1 min

#### Canción 3 (modo: Letra automática)
- **Título:** `Pa' Que Sufras`
- **Tags a clickear:** `ranchera` · `sad` · `melancholic` · `slow`
- **Prompt de estilo:**
  ```
  guitar, trumpet, 75bpm, traditional mexican
  ```
- **Descripción de letra:**
  ```
  Ranchera sobre una traición amorosa, el dolor del abandono, la dignidad de quien sufrió pero saldrá adelante. Estilo Vicente Fernández: dramático, con sentimiento, con gritos de mariachi entre los versos.
  ```
- **Duración:** 1 min

#### Canción 4 (modo: Letra automática)
- **Título:** `Cumbia del Barrio`
- **Tags a clickear:** `cumbia` · `happy` · `playful`
- **Prompt de estilo:**
  ```
  latin, 120bpm, accordion, percussion, tropical
  ```
- **Descripción de letra:**
  ```
  Cumbia festiva sobre el orgullo del barrio donde creciste, las noches de fiesta en la cuadra, los amigos de infancia, la alegría simple de la comunidad. Tono celebratorio y cálido.
  ```
- **Duración:** 1 min

#### Canción 5 (modo: Letra exacta)
- **Título:** `Generación Rota`
- **Tags a clickear:** `rock` · `angry` · `dark` · `fast`
- **Prompt de estilo:**
  ```
  135bpm, electric guitar, drum kit, alternative, grunge influence
  ```
- **Letra:**
  ```
  Nos vendieron un sueño de plástico
  nos dijeron que todo va bien
  Pero aquí abajo el sonido es estático
  y nadie responde al "¿por qué?"

  Somos la generación rota
  que aprendió a sonreír igual
  Con el ruido en la garganta
  y las ganas de no callar
  ```
- **Duración:** 1 min

#### Canción 6 (modo: Letra exacta)
- **Título:** `Jopping en Español`
- **Tags a clickear:** `kpop` · `playful` · `energetic`
- **Prompt de estilo:**
  ```
  upbeat, 130bpm, synth, pop, idol
  ```
- **Letra:**
  ```
  Me levanté con todo el power
  hoy el mundo es mío lo sé
  Con el beat corriendo en la sangre
  nadie me para esta vez

  Jopping en español baby
  esto es lo que hay
  Seguimos el ritmo juntos
  no te quedes atrás
  ```
- **Duración:** 1 min

---

## 5. Resumen de canciones por gustos (para recomendaciones)

| # | Usuario | Título | Géneros principales |
|---|---------|--------|-------------------|
| 1-6 | cliente1 | Lluvia de Medianoche, Café con Jazz, 3AM Biblioteca, Reencuentro, Otoño, Lo Que Queda | lofi, jazz, chill, melancholic, nostalgic |
| 7-12 | cliente2 | Noches sin Señal, Domingo Gris, Señales de Humo, Último Verano, El Cuarto, Fade Out | lofi, pop, sad, chill, nostalgic |
| 13-18 | cliente3 | La Calle Pide Más, Noche de Fiesta, El Ritmo, Baila Conmigo, Del Barrio, Esta Noche | reggaeton, pop, energetic, happy, latin |
| 19-24 | cliente4 | Tu Nombre, Bachata en el Alma, Pegados, Lo Que Promete, Veneno Dulce, Contigo | reggaeton, bachata, romantic, latin |
| 25-30 | cliente5 | Distorsión, Idol Vibes, Pa' Que Sufras, Cumbia, Generación Rota, Jopping | rock, kpop, ranchera, cumbia, diverse |

**Grupos de similaridad esperados:**
- `cliente1 ↔ cliente2` → lofi · chill · nostalgic en común
- `cliente3 ↔ cliente4` → reggaeton · latin · energetic en común

---

## 6. Fase 3 — Biblioteca personal

**Cada persona hace esto después de que sus canciones terminen de generarse.**

1. Ir a **Tu biblioteca** en el sidebar
2. Verificar que aparecen las 6 canciones (puede tardar si Celery está procesando)
3. Hacer clic en el botón ▶ de una canción → se abre el mini player en la parte inferior
4. Verificar que el audio reproduce correctamente
5. Probar el buscador: escribir parte del título → filtrar
6. Probar los botones de orden: **Recientes**, **Antiguas**, **A-Z**
7. Hacer clic en el botón **+ Crear Canción** → verifica que redirige a `/create`

**Qué verificar:**
- [ ] Las 6 canciones aparecen con título y tags
- [ ] El mini player reproduce audio real (no silencio)
- [ ] Los filtros funcionan
- [ ] El botón de like (❤) en la tarjeta incrementa el contador

---

## 7. Fase 4 — Publicar en comunidad

**Antes de probar el feed comunitario, cada persona debe publicar algunas canciones.**

1. Ir a **Tu biblioteca**
2. Para cada una de las canciones que querés publicar: hacer clic en la tarjeta (o en el botón de editar si existe)
3. En los detalles de la canción, activar la opción **Publicar en comunidad** (toggle `is_public`)
4. Guardar

**Qué publicar por persona:**
- Persona 1: publicar canciones 1, 3 y 5 (las de géneros lofi/jazz)
- Persona 2: publicar canciones 2, 4 y 6 (las de géneros pop/chill)
- Persona 3: publicar todas las 6 (reggaeton/pop muy shareable)
- Persona 4: publicar canciones 1, 2 y 4 (reggaeton y bachata)
- Persona 5: publicar canciones 2, 4 (kpop y cumbia — más accesibles)

**Total esperado en feed:** ~17 canciones públicas

> **Alternativa si no hay botón de toggle en la UI todavía:** Usar el endpoint directamente vía curl:
> ```bash
> curl -X PATCH https://tu-api.railway.app/api/songs/<song-uuid>/ \
>   -H "Authorization: Bearer <tu-token>" \
>   -H "Content-Type: application/json" \
>   -d '{"is_public": true}'
> ```
> El token lo obtenés desde DevTools → Application → LocalStorage → `auth-storage` → `accessToken`

---

## 8. Fase 5 — Comunidad

**Todas las personas, una por una o en paralelo.**

1. Ir a **Comunidad** en el sidebar
2. **Verificar stats reales:** los números de canciones publicadas, usuarios activos y reproducciones son datos reales (no hardcodeados). Deben coincidir con lo que hay en la BD.
3. **Navegar el feed:** desplazar hacia abajo, ver las tarjetas de canciones de los demás usuarios
4. **Probar el buscador:** escribir "reggaeton" → filtrar. Escribir "lofi" → filtrar. Limpiar.
5. **Probar filtros por tag:** clic en "reggaeton" → solo canciones de reggaeton. Clic en "lofi" → solo lofi. Clic en "Todos" → vuelve todo.
6. **Dar like:** en cada canción del feed, hacer clic en el botón ❤ → el contador debe subir. Hacer clic de nuevo → debe bajar (toggle).
7. **Reproducir:** clic en el botón ▶ blanco → el audio debe cargar y sonar. El contador de reproducciones en el servidor debe subir (verificar después en el panel admin o refrescando la página).
8. **Cargar más:** hacer clic en "Ver más" si aparece → carga la siguiente página.

**Qué verificar:**
- [ ] Feed muestra canciones reales de otros usuarios
- [ ] Stats muestran números reales
- [ ] Like sube/baja al hacer clic
- [ ] Audio reproduce desde S3
- [ ] Filtro por tag funciona
- [ ] "Ver más" carga más canciones

---

## 9. Fase 6 — Stems / Karaoke

> **Requiere 2 créditos por separación.** Verificar que tienen créditos disponibles antes.
> El servidor Modal también procesa esto, así que va a la cola de Celery.

**Persona 1 hace esta prueba primero. Las demás pueden repetirla después.**

1. Ir a **Separar pistas** en el sidebar
2. **Panel izquierdo — Subir archivo:**
   - Clic en la zona de drag & drop o el botón de seleccionar archivo
   - Seleccionar un archivo `.mp3` o `.wav` de hasta 50MB (puede ser cualquier canción descargada)
   - Verificar que muestra el nombre del archivo y su tamaño
3. Clic en **Separar pistas (2 créditos)**
4. Verificar que el crédito baja de 20 a 18 en el header
5. La barra de progreso aparece: En cola → Separando pistas (0%…10%…80%…100%)
6. Al completarse, aparecen los botones de **Vocals** y **Karaoke**:
   - Clic en ▶ junto a "Karaoke" → reproduce la versión sin voz
   - Clic en ▶ junto a "Vocals" → reproduce solo la voz
   - Clic en ⬇ Descargar → descarga el archivo WAV

**Panel derecho — Historial:**
- Después de completar la separación, en el panel derecho aparece el job con el status `completed`

**Pruebas de error (Persona 2):**
- Intentar subir un archivo `.txt` → debe rechazarlo con mensaje
- Intentar subir un archivo mayor a 50MB → debe rechazarlo con mensaje de tamaño

**Qué verificar:**
- [ ] La zona de drop acepta .mp3 y .wav
- [ ] Rechaza archivos incorrectos con mensaje claro
- [ ] La barra de progreso avanza en tiempo real (polling cada 3s)
- [ ] Al completarse aparecen los stems descargables
- [ ] El historial muestra el job con status

---

## 10. Fase 7 — Playlists

### 10.1 Playlists manuales

**Persona 1:**
1. Ir a **Playlists** en el sidebar
2. Clic en **+ Nueva playlist**
3. Nombre: `Mis Noches de Lluvia` → Enter o clic Crear
4. La playlist aparece en la grilla con badge "Manual" y 0 canciones
5. Clic en la playlist → abre `PlaylistDetailPage`
6. Verificar que muestra: título, descripción vacía, "0 canciones"

**Agregar canciones a la playlist** (requiere tener canciones en biblioteca):
> Por ahora el flujo es: ir a la biblioteca, copiar el UUID de la canción desde la URL, y llamar al endpoint. En la siguiente iteración habrá un botón "Agregar a playlist" en la tarjeta.
>
> Por el momento, probar el endpoint directamente:
> ```bash
> curl -X POST https://tu-api.railway.app/api/playlists/<playlist-uuid>/songs/ \
>   -H "Authorization: Bearer <token>" \
>   -H "Content-Type: application/json" \
>   -d '{"song_id": "<song-uuid>", "position": 0}'
> ```

7. Probar el botón **Compartir** en PlaylistDetailPage:
   - Clic → genera un link público y lo copia al portapapeles
   - Abrir el link en una ventana de incógnito o en la computadora de otra persona → debe mostrar la playlist sin requerir login

**Persona 2** prueba la playlist pública de Persona 1 en su propio navegador.

### 10.2 Playlists automáticas

1. En la página Playlists → ir a la pestaña **Automáticas**
2. Clic en **↺ Regenerar**
3. El sistema genera playlists agrupando canciones por mood y género
4. Verificar que aparecen playlists como:
   - "Canciones Chill" (si el usuario tiene canciones con tag `chill`)
   - "Canciones Energetic" (si tiene canciones energéticas)
   - "Mis canciones de Lofi" (si tiene canciones de lofi)
5. Clic en una playlist automática → ver la lista de canciones

**Qué verificar:**
- [ ] Se puede crear una playlist manual
- [ ] El nombre se guarda correctamente
- [ ] El link de compartir funciona sin login
- [ ] Las playlists automáticas se generan con canciones reales
- [ ] Las playlists aparecen agrupadas por tipo (Manual / Auto)

---

## 11. Fase 8 — Recomendaciones

> **Esta fase requiere que las fases anteriores estén completas:** canciones publicadas + fases de comunidad (plays/likes) ejecutadas.
>
> El sistema de recomendaciones usa `UserTasteProfile` que se calcula a partir del `ListeningHistory`. Este historial se pobla cuando alguien escucha canciones en el feed de comunidad.

**Paso 1 — Generar historial de escucha:**
Cada persona debe reproducir al menos 5-6 canciones en la sección Comunidad (fase 5) antes de hacer esto.

**Paso 2 — Verificar el perfil de gustos:**
```bash
# Ver el perfil de gustos del usuario logueado:
GET https://tu-api.railway.app/api/recommendations/suggested-tags/
```
Debe devolver los tags más reproducidos.

**Paso 3 — Abrir "Para ti":**
1. Ir a **Para ti** en el sidebar
2. Verificar que aparecen canciones de otros usuarios que comparten tags similares
3. **Persona 1** debería ver canciones de **Persona 2** (lofi/chill en común)
4. **Persona 3** debería ver canciones de **Persona 4** (reggaeton/latin en común)
5. Los chips de "Tus géneros favoritos" deben mostrar los tags que más reprodujiste

**Qué verificar:**
- [ ] El feed "Para ti" no está vacío
- [ ] Las canciones sugeridas pertenecen a otros usuarios
- [ ] Los tags sugeridos coinciden con los géneros que más escuchaste
- [ ] Personas con gustos similares se ven mutuamente en recomendaciones

> **Si las recomendaciones están vacías:** Volver a la fase de Comunidad, reproducir más canciones de varios géneros, esperar ~1 minuto para que el historial se actualice, y volver a Para ti.

---

## 12. Fase 9 — Mix DJ

> **Requiere 3 créditos para exportar.** Verificar créditos disponibles.

### 12.1 Crear proyecto de mix

**Persona 3 hace la demo completa, las demás observan y luego repiten.**

1. Ir a **Mix DJ** en el sidebar
2. Clic en **+ Nuevo proyecto**
3. Nombre: `My First Mix`
4. Clic **Crear** → redirige al editor del mix

### 12.2 Agregar clips

En el editor (MixEditorPage):
1. Clic en **+ Agregar** en el panel izquierdo
2. Se abre el modal → pestaña **Biblioteca**
3. Clic en una canción → se agrega como Clip 1
4. Clic en otra canción → Clip 2
5. Clic en otra → Clip 3
6. Cerrar el modal

### 12.3 Editar clips

1. Clic en el Clip 1 en el panel izquierdo → se expande con controles
2. En el panel derecho (detalle del clip seleccionado):
   - **Inicio (ms):** cambiar de 0 a `5000` → el clip empieza 5 segundos adentro
   - **Fin (ms):** ajustar a `35000` → el clip dura 30 segundos
   - **Fade in:** mover slider a `1000ms`
   - **Fade out:** mover slider a `1500ms`
   - **Volumen:** mover slider a `90%`
3. Repetir ajustes para el Clip 2 con valores distintos

### 12.4 Timeline

Verificar que la barra de timeline muestra:
- Los clips en orden proporcional a su duración
- Colores distintos por clip
- El clip seleccionado aparece resaltado

### 12.5 Exportar

1. Clic en **Exportar** (botón superior derecho)
2. Seleccionar formato: **MP3**
3. Calidad: **320 kbps**
4. Clic **Exportar (3 créditos)**
5. Aparece spinner "Procesando tu mix..."
6. Cuando termina aparece botón **⬇ Descargar MP3**
7. Descargar y reproducir en el reproductor del sistema → verificar que suena correcto

### 12.6 Probar con stems (Persona 4)

1. Crear un nuevo proyecto de mix
2. Agregar clip → ir a pestaña **Stems separados**
3. Seleccionar un stem de karaoke de la fase anterior
4. Agregar también una canción normal
5. Exportar como WAV → verificar descarga

**Qué verificar:**
- [ ] Se puede crear un proyecto
- [ ] El modal muestra canciones de la biblioteca y stems separados
- [ ] Los controles de inicio/fin, fade y volumen se guardan
- [ ] La exportación genera un archivo descargable
- [ ] El archivo descargado reproduce correctamente

---

## 13. Fase 10 — Panel de administración

**Solo el admin (admin@musicgen.com / admin1234) hace esto.**

1. Cerrar sesión de cualquier cuenta de cliente
2. Ir a `/login` → entrar como `admin@musicgen.com` / `admin1234`
3. El sistema detecta rol admin y redirige a `/admin`

### 13.1 Dashboard

En `/admin`:
- Verificar que las 6 stat cards muestran números (aunque sean datos demo del DashboardPage)

### 13.2 Usuarios

En `/admin/usuarios`:
1. Verificar que la tabla carga todos los usuarios del seeder
2. Buscar "cliente1" → filtrar correctamente
3. Buscar "lofi" → 0 resultados (no es un usuario)
4. Limpiar búsqueda → vuelven todos
5. Verificar badges de rol (admin/usuario) y estado (activo/inactivo)

### 13.3 Reportes

En `/admin/reportes`:
1. Verificar que los 6 stat cards muestran datos reales:
   - **Total usuarios** → debe ser ~41
   - **Canciones generadas** → debe ser ~30 (las que generamos)
   - **Canciones públicas** → las que publicamos en la fase 4
   - **Jobs fallidos** → idealmente 0
2. En la tabla **Top canciones públicas** deben aparecer las canciones más reproducidas
3. Verificar que los tags de cada canción se muestran como chips

### 13.4 Roles y Planes

- `/admin/roles` → ver que existen los 2 roles del sistema (admin, user)
- `/admin/planes` → verificar los 3 planes (Free, Pro, Studio) con precios correctos

**Qué verificar:**
- [ ] Login como admin redirige a /admin (no a /)
- [ ] Tabla de usuarios carga y busca correctamente
- [ ] Reportes muestran datos reales (no mock)
- [ ] Planes se pueden ver

---

## 14. Checklist Final de Verificación

### Módulo: Auth
- [ ] Login con cliente1-5 funciona
- [ ] Login con credenciales incorrectas muestra error
- [ ] El balance de 20 créditos aparece en el header
- [ ] Logout cierra sesión y redirige a /login

### Módulo: Songs
- [ ] Los 3 modos de generación funcionan (descripción, letra automática, letra exacta)
- [ ] El job status cambia: queued → processing → ready
- [ ] La canción aparece en biblioteca con audio reproducible
- [ ] El thumbnail/cover se genera y muestra
- [ ] El crédito se descuenta correctamente (20→19→18...)

### Módulo: Community
- [ ] Feed muestra canciones públicas de otros usuarios
- [ ] Like toggle funciona (sube/baja contador)
- [ ] Play graba la reproducción
- [ ] Stats muestran datos reales
- [ ] Filtro por tag funciona
- [ ] Paginación "Ver más" carga más canciones

### Módulo: Stems
- [ ] Upload de .mp3 funciona
- [ ] Archivos incorrectos son rechazados
- [ ] Separación completada muestra vocals y karaoke
- [ ] Descarga de stems funciona

### Módulo: Playlists
- [ ] Crear playlist manual funciona
- [ ] Playlist aparece en la grilla
- [ ] Compartir genera link público
- [ ] Link público accesible sin login
- [ ] Playlists automáticas se generan al hacer "Regenerar"

### Módulo: Recommendations
- [ ] "Para ti" muestra canciones de otros usuarios
- [ ] Tags sugeridos coinciden con gustos del usuario
- [ ] Usuario 1 ve canciones del usuario 2 (lofi en común)
- [ ] Usuario 3 ve canciones del usuario 4 (reggaeton en común)

### Módulo: Mix DJ
- [ ] Crear proyecto funciona
- [ ] Agregar clips desde biblioteca funciona
- [ ] Ajustar inicio/fin/fade/volumen se guarda
- [ ] Exportar MP3/WAV genera archivo descargable
- [ ] Archivo descargado reproduce correctamente

### Módulo: Notifications
- [ ] Bell icon muestra badge cuando hay notificaciones no leídas
- [ ] Dropdown abre al hacer clic
- [ ] Las notificaciones de "canción lista", "stems listos", "mix exportado" aparecen
- [ ] "Marcar todas leídas" limpia el badge

### Panel de Admin
- [ ] Login como admin redirige a /admin
- [ ] Tabla de usuarios muestra todos los usuarios
- [ ] Búsqueda de usuarios funciona
- [ ] Reportes muestran datos reales
- [ ] Planes se visualizan correctamente

---

## Apéndice A — Mensajes de error esperados

| Situación | Mensaje esperado |
|-----------|-----------------|
| Sin créditos suficientes | HTTP 402 — "Sin créditos disponibles." |
| Archivo stem muy grande (>50MB) | "El archivo excede el límite de 50MB." |
| Archivo stem tipo incorrecto | Mensaje de validación en el uploader |
| Mix sin clips al exportar | "El mix no tiene clips." |
| Credenciales incorrectas | "No active account found with the given credentials" |
| Token expirado | Auto-refresh silencioso; si falla → redirige a login |

## Apéndice B — Orden de créditos por acción

| Acción | Costo |
|--------|-------|
| Generar canción | 1 crédito |
| Separar stems | 2 créditos |
| Exportar mix | 3 créditos |
| Like / Play / Playlist | 0 créditos |

**Con 20 créditos iniciales:**
- 6 canciones = 6 créditos
- 1 separación de stems = 2 créditos
- 1 exportación de mix = 3 créditos
- **Total usado = 11 créditos → quedan 9 de margen**

## Apéndice C — Verificación rápida de API

Podés hacer estas llamadas desde Postman o curl para verificar que el backend está respondiendo antes de abrir el frontend:

```bash
# Health check básico
curl https://tu-api.railway.app/api/auth/login/ -X POST \
  -H "Content-Type: application/json" \
  -d '{"email": "cliente1@gmail.com", "password": "cliente1234"}'
# Esperado: {"access": "...", "refresh": "..."}

# Verificar tags (no requiere auth)
curl https://tu-api.railway.app/api/songs/tags/
# Esperado: array con 35 tags

# Verificar planes
curl https://tu-api.railway.app/api/credits/plans/
# Esperado: Free, Pro, Studio
```

---

*Guía generada para el proyecto Generador Musical UAGRM — Sprint final de pruebas.*
