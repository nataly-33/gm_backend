# Guía: Redis + Celery en Windows (PowerShell) — Opción WSL2

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

## 1. Verificar WSL2

```powershell
# Verificar que WSL2 está instalado
wsl --list --verbose

# Si no está instalado (requiere reinicio):
wsl --install
```

---

## 2. Instalar Redis dentro de WSL2

```powershell
# Solo la primera vez
wsl sudo apt update
wsl sudo apt install redis-server -y
```

---

## 3. Configurar Redis para que Windows pueda conectarse

> ⚠️ **Este paso es obligatorio.** Por defecto Redis en WSL2 solo escucha dentro de la VM Linux. Sin este cambio, Python en Windows recibe `Error 10061 connection refused`.

Abrí una terminal WSL2 (escribí `wsl` en PowerShell) y ejecutá:

```bash
# 1. Cambiar bind a todas las interfaces
sudo sed -i 's/^bind 127.0.0.1.*/bind 0.0.0.0/' /etc/redis/redis.conf

# 2. Verificar que quedó bien (debe mostrar: bind 0.0.0.0)
grep "^bind" /etc/redis/redis.conf
```

---

## 4. Iniciar Redis

```powershell
# Iniciar el servidor Redis dentro de WSL2
wsl sudo service redis-server start

# Verificar que está corriendo (debe responder PONG)
wsl redis-cli ping
```

---

## 5. Verificar la conexión Redis desde Python

Con el venv activado, desde `gm_backend/`:

```powershell
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
# Debe imprimir: True
```

---

## 6. Iniciar el Worker de Celery

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

## 7. Verificar que el worker responde

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

## 8. Flujo completo de desarrollo

```
Terminal 1 (PowerShell) →  python manage.py runserver
Terminal 2 (PowerShell) →  celery -A workers.celery worker -l info --pool=solo
Terminal 3 (WSL2)       →  sudo service redis-server start
```

---

## 9. Detener Redis

```powershell
wsl sudo service redis-server stop
```

---

## Resumen rápido de comandos

| Acción | Comando |
| :--- | :--- |
| Instalar Redis (primera vez) | `wsl sudo apt install redis-server -y` |
| Configurar bind (primera vez) | En terminal WSL2: `sudo sed -i 's/^bind 127.0.0.1.*/bind 0.0.0.0/' /etc/redis/redis.conf` |
| Iniciar Redis | `wsl sudo service redis-server start` |
| Verificar Redis | `wsl redis-cli ping` |
| Verificar desde Python | `python -c "import redis; print(redis.from_url('redis://localhost:6379/0').ping())"` |
| Iniciar Celery worker | `celery -A workers.celery worker -l info --pool=solo` |
| Verificar worker activo | `celery -A workers.celery inspect ping` |
| Ver tareas registradas | `celery -A workers.celery inspect registered` |
| Detener Redis | `wsl sudo service redis-server stop` |

---

## Errores comunes

| Error | Causa | Solución |
| :--- | :--- | :--- |
| `Error 10061 connection refused` | Redis no configurado con `bind 0.0.0.0` o no está corriendo | Seguir el paso 3 y luego iniciar Redis |
| `PermissionError WinError 5` | Celery usa `fork` en Windows | Agregar `--pool=solo` |
| `No module named 'config'` | Script corrido desde carpeta incorrecta | Correr desde `gm_backend/` |
| `PONG` no responde desde Python pero sí desde `wsl redis-cli` | Redis escucha solo en WSL2 (`bind 127.0.0.1`) | Seguir el paso 3 |
