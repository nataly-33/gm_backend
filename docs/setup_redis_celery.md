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
sudo nano /etc/redis/redis.conf
#protected-mode yes → cambiá el yes por no. 

# 2. Verificar que quedó bien (debe mostrar: bind 0.0.0.0)
sudo grep "^bind" /etc/redis/redis.conf
#wsl sudo grep "^bind" /etc/redis/redis.conf
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
| Celery dice "ready" y a los pocos segundos pierde la conexión | WSL2 se apagó automáticamente matando Redis | Ver sección "Error: WSL2 se apaga solo" abajo |
| `CPendingDeprecationWarning: In Celery 5.1 we introduced...` | Falta `broker_connection_retry_on_startup = True` en config | Ver sección "Warnings de deprecación" abajo |

---

## Error: WSL2 se apaga solo y mata Redis

### Síntomas

```
[22:28:23] celery@PC ready.
[22:28:29] consumer: Connection to broker lost. Trying to re-establish...
ConnectionRefusedError: [WinError 10061] No connection could be made...
```

Celery dice "ready" y entre 5 y 30 segundos después pierde la conexión aunque Redis parecía estar bien.

### Causa

WSL2 funciona como una máquina virtual Linux que se apaga **automáticamente ~8 segundos después de que el último proceso WSL2 cierra su terminal**. Si iniciaste Redis con `wsl sudo service redis-server start` y luego cerraste esa terminal PowerShell, WSL2 se apagó y Redis murió con él.

El error `WinError 10061` confirma que nada está escuchando en el puerto 6379 — el proceso dejó de existir.

### Solución A — Mantener WSL2 vivo (rápida)

En lugar de `wsl sudo service redis-server start` usá este comando, que inicia Redis **y mantiene WSL2 despierto** con un proceso `tail` que nunca termina:

```powershell
# Terminal 3 — NO cerrar mientras estés desarrollando
wsl bash -c "sudo service redis-server start && tail -f /dev/null"
```

Dejá esa terminal abierta. Mientras `tail -f /dev/null` esté corriendo, WSL2 no se apagará y Redis seguirá vivo.

Para detenerlo: `Ctrl+C` en esa terminal.

### Solución B — Docker (más estable, recomendada para el grupo)

Docker corre Redis como un proceso nativo de Windows. No depende de WSL2 ni de terminales abiertas. Si tenés Docker Desktop instalado:

```powershell
# Solo la primera vez — crea el contenedor
docker run -d --name redis-gm -p 6379:6379 --restart always redis:alpine

# Verificar que responde
docker exec redis-gm redis-cli ping
# Debe imprimir: PONG
```

Con `--restart always`, Docker reinicia el contenedor solo si cae o si reiniciás Windows. No hay que hacer nada más cada vez que abrís el proyecto.

```powershell
# Si ya existe el contenedor y solo querés iniciarlo
docker start redis-gm

# Detenerlo
docker stop redis-gm
```

### Verificación post-fix

Después de aplicar cualquiera de las dos soluciones:

```powershell
# Debe responder True
python -c "import redis; print(redis.from_url('redis://localhost:6379/0').ping())"
```

---

## Warnings de deprecación en Celery 5.x

### Síntoma

```
CPendingDeprecationWarning: In Celery 5.1 we introduced an optional breaking change...
worker_cancel_long_running_tasks_on_connection_loss...
```

Estos mensajes no rompen nada, pero indican que la configuración de Celery está incompleta para la versión 5.x.

### Causa

Celery 5.1+ introdujo settings nuevos que no estaban en la config original del proyecto.

### Solución

El archivo `workers/celery.py` ya fue actualizado con estas líneas. Si no las tenés, agregalas:

```python
# workers/celery.py — después de app.autodiscover_tasks()

app.conf.broker_connection_retry_on_startup = True   # elimina el CPendingDeprecationWarning
app.conf.broker_connection_retry            = True   # reintenta si Redis cae y vuelve
app.conf.broker_connection_max_retries      = None   # reintentar indefinidamente
app.conf.broker_heartbeat                   = 10     # detecta caídas en ~10s
app.conf.broker_transport_options = {
    'visibility_timeout': 3600,
    'socket_keepalive':   True,
}
app.conf.worker_cancel_long_running_tasks_on_connection_loss = True
```

Con esto:
- Los warnings de deprecación desaparecen
- Si Redis cae y vuelve (reinicio, reconexión WSL2), Celery se reconecta automáticamente sin que tengas que reiniciarlo manualmente

---

## Flujo completo actualizado de desarrollo

```
Terminal 1 (PowerShell) →  python manage.py runserver
Terminal 2 (PowerShell) →  celery -A workers.celery worker -l info --pool=solo
Terminal 3 (PowerShell) →  wsl bash -c "sudo service redis-server start && tail -f /dev/null"
                            (o simplemente: docker start redis-gm  si usás Docker)
```

> **Regla de oro:** La terminal 3 de Redis **nunca se cierra** mientras estés trabajando. Si accidentalmente la cerrás, Redis muere y Celery empieza a tirar `Error 10061`. Solución: volver a abrir la terminal y ejecutar el comando de Redis de nuevo. Celery se reconecta solo gracias a la config actualizada.
