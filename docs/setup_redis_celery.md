# Guía: Redis + Celery en Windows (PowerShell)

> **¿Cuándo necesitás esto?**
> Redis y Celery se usan solo cuando implementes la generación de canciones asíncrona (Sprint 1, Persona B).
> Para correr el servidor Django, el seed y los endpoints de auth **no los necesitás**.

---

## ¿Para qué sirven en este proyecto?

```
Usuario → POST /api/songs/generate/
           ↓
        Django encola la tarea en Redis (broker)
           ↓
        Celery worker la toma de la cola
           ↓
        Llama a Modal AI → genera el MP3
           ↓
        Guarda en S3 → actualiza la BD → notifica al usuario
```

- **Redis** = cola de mensajes (broker). Guarda las tareas pendientes.
- **Celery** = worker que procesa esas tareas en segundo plano.
- Sin Redis corriendo, Celery no puede conectarse. Sin Celery corriendo, las tareas se acumulan en Redis pero nadie las procesa.

---

## 1. Instalar Redis en Windows

### Opción A — WSL2 (recomendada, viene con Windows 11)

```powershell
# Verificar que WSL2 está instalado
wsl --list --verbose

# Si no está instalado (requiere reinicio):
wsl --install
```

Una vez que tenés WSL2 con Ubuntu, instalá Redis dentro:

```powershell
# Instalar Redis dentro de WSL2 (solo la primera vez)
wsl sudo apt update
wsl sudo apt install redis-server -y
```

### Opción B — Scoop (gestor de paquetes para Windows)

```powershell
# Instalar Scoop si no lo tenés
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# Instalar Redis con Scoop
scoop install redis
```

### Opción C — Chocolatey

```powershell
# Requiere Chocolatey instalado (https://chocolatey.org/)
choco install redis -y
```

---

## 2. Iniciar Redis

### Si usás WSL2 (Opción A):

```powershell
# Iniciar el servidor Redis dentro de WSL2
wsl sudo service redis-server start

# Verificar que está corriendo (debe responder PONG)
wsl redis-cli ping
```

### Si usás Scoop/Chocolatey (Opciones B y C):

```powershell
# Iniciar Redis como proceso
redis-server

# En otra terminal, verificar:
redis-cli ping
```

---

## 3. Verificar la conexión Redis desde Python

Con el venv activado, desde `gm_backend/`:

```powershell
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
# Debe imprimir: True
```

---

## 4. Iniciar el Worker de Celery

> ⚠️ **Windows requiere `--pool=solo`** — sin esta flag aparece un `PermissionError` en Windows.

Abrí una **nueva terminal PowerShell** (la segunda), activá el venv y ejecutá:

```powershell
# Desde gm_backend/
venv\Scripts\activate
celery -A workers.celery worker -l info --pool=solo
```

Deberías ver algo como:
```
[config]
.> app:         gm
.> transport:   redis://localhost:6379/0
.> results:     redis://localhost:6379/0
.> concurrency: 1 (solo)

[queues]
.> celery  exchange=celery(direct) key=celery

[tasks]
  (ninguna tarea registrada todavía — se agregan en cada app)

[2026-05-09 22:00:00,000: INFO/MainProcess] celery@HOSTNAME ready.
```

---

## 5. Verificar que el worker responde

En una **tercera terminal** (con venv activado):

```powershell
celery -A workers.celery inspect ping
```

Respuesta esperada:
```
-> celery@HOSTNAME: OK
   pong
```

---

## 6. Flujo completo de desarrollo

```
Terminal 1  →  python manage.py runserver          (Django API)
Terminal 2  →  celery -A workers.celery worker -l info --pool=solo  (Worker)
Terminal 3  →  wsl sudo service redis-server start  (Redis, solo WSL2)
```

Con Scoop/Chocolatey, Redis puede correr como servicio en background:
```powershell
# Registrar Redis como servicio de Windows (Scoop)
redis-server --service-install
Start-Service redis
```

---

## 7. Detener Redis

```powershell
# WSL2:
wsl sudo service redis-server stop

# Windows nativo:
redis-cli shutdown
# o desde el administrador de servicios si está instalado como servicio
```

---

## Resumen rápido de comandos

| Acción | Comando PowerShell |
| :--- | :--- |
| Iniciar Redis (WSL2) | `wsl sudo service redis-server start` |
| Verificar Redis | `wsl redis-cli ping` |
| Verificar desde Python | `python -c "import redis; print(redis.from_url('redis://localhost:6379/0').ping())"` |
| Iniciar Celery worker | `celery -A workers.celery worker -l info --pool=solo` |
| Verificar worker activo | `celery -A workers.celery inspect ping` |
| Ver tareas registradas | `celery -A workers.celery inspect registered` |
| Detener Redis (WSL2) | `wsl sudo service redis-server stop` |

---

## Errores comunes

| Error | Causa | Solución |
| :--- | :--- | :--- |
| `Error 10061 connection refused` | Redis no está corriendo | Iniciá Redis primero |
| `PermissionError WinError 5` | Celery usa `fork` en Windows | Agregar `--pool=solo` |
| `No module named 'config'` | Script corrido desde carpeta incorrecta | Correr desde `gm_backend/` |
| `PONG` no responde | Puerto 6379 bloqueado por firewall | Revisar reglas del firewall de Windows |
