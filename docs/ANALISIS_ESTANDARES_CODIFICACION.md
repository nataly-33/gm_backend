# Estándares de Codificación — Proyecto Generación Musical

> **Versión:** 2.0 — 2026-06-17
> **Aplica a:** `gm_backend` (Django/Python) · `gm_frontend` (React/TypeScript)
> **Basado en:** Angular Style Guide · ISO/IEC 25010:2011 · Microsoft TypeScript Guidelines · Clean Code (R. C. Martin) · Principios SOLID · PEP 8 · Google Python Style Guide

---

## Tabla de Contenidos

1. [Frontend — TypeScript / React](#1-frontend--typescript--react)
   - 1.1 [Convención de Nombres](#11-convención-de-nombres)
   - 1.2 [Documentación y JSDoc](#12-documentación-y-jsdoc)
   - 1.3 [Orden de Importaciones](#13-orden-de-importaciones)
   - 1.4 [Tipado TypeScript](#14-tipado-typescript)
   - 1.5 [Estructura de Archivos y Carpetas](#15-estructura-de-archivos-y-carpetas)
   - 1.6 [Componentes React](#16-componentes-react)
   - 1.7 [Custom Hooks](#17-custom-hooks)
   - 1.8 [Gestión de Estado (Zustand)](#18-gestión-de-estado-zustand)
   - 1.9 [Capa de API](#19-capa-de-api)
   - 1.10 [Routing y Lazy Loading](#110-routing-y-lazy-loading)
   - 1.11 [Estilos y CSS](#111-estilos-y-css)
   - 1.12 [Manejo de Errores](#112-manejo-de-errores)
2. [Backend — Python / Django](#2-backend--python--django)
   - 2.1 [Convención de Nombres](#21-convención-de-nombres)
   - 2.2 [Documentación y Docstrings](#22-documentación-y-docstrings)
   - 2.3 [Type Hints](#23-type-hints)
   - 2.4 [Estructura de Apps Django](#24-estructura-de-apps-django)
   - 2.5 [Modelos](#25-modelos)
   - 2.6 [Vistas (Views)](#26-vistas-views)
   - 2.7 [Serializers](#27-serializers)
   - 2.8 [Servicios (Services)](#28-servicios-services)
   - 2.9 [Tareas Celery](#29-tareas-celery)
   - 2.10 [Manejo de Excepciones](#210-manejo-de-excepciones)
   - 2.11 [Seguridad y Configuración](#211-seguridad-y-configuración)
3. [Herramientas y Configuración](#3-herramientas-y-configuración)
   - 3.1 [Frontend](#31-frontend)
   - 3.2 [Backend](#32-backend)
   - 3.3 [Pre-commit Hooks](#33-pre-commit-hooks)
4. [Referencias](#4-referencias)

---

## 1. Frontend — TypeScript / React

### 1.1 Convención de Nombres

El proyecto usa tres convenciones diferenciadas según el tipo de elemento.

#### UpperCamelCase — Clases, Interfaces, Tipos y Componentes

Usar para: clases, interfaces, type aliases, enums y componentes React.

```typescript
// ✅ Correcto — Interfaz de usuario del store
interface AuthUser {
  id: string
  email: string
  full_name: string
  credit_balance: number
  role: string
}

// ✅ Correcto — Type alias de opciones de ordenamiento
type SortOption = 'recent' | 'oldest' | 'title'

// ✅ Correcto — Componente React
export default function SongCard({ song, onPlay }: SongCardProps) {
  return <article>...</article>
}

// ❌ Incorrecto — prefijo I en interfaces
interface IAuthUser {}

// ❌ Incorrecto — lowerCamelCase en interfaces
interface authUser {}
```

#### lowerCamelCase — Variables, Funciones, Props y Hooks

Usar para: variables, funciones, métodos, argumentos y custom hooks.

```typescript
// ✅ Correcto — variables de estado
const [songs, setSongs] = useState<LibrarySong[]>([])
const [loading, setLoading] = useState(true)
const [activeUrl, setActiveUrl] = useState<string | null>(null)

// ✅ Correcto — funciones handler (prefijo "handle" o "on")
async function handlePlay(song: LibrarySong) {
  const url = await getSongPlayUrl(song.id)
  setActiveUrl(url)
}

// ✅ Correcto — custom hook con prefijo "use"
export function useStemJob(jobId: string | null) {
  const [status, setStatus] = useState<string | null>(null)
  return { status }
}

// ✅ Correcto — props con prefijo "on" para callbacks
interface SongCardProps {
  song: LibrarySong
  onPlay?: (song: LibrarySong) => void
  onDelete?: (songId: string) => void
}
```

#### lowercase-with-hyphens — Archivos, Módulos y Directorios

**Todos** los archivos `.tsx`, `.ts` y `.css` del proyecto usan kebab-case.

```
// ✅ Correcto — nombres de archivos
song-card.tsx
library-page.tsx
song-card.module.css
auth-layout.tsx
use-stem-job.ts
auth.store.ts       ← excepción aceptada: punto como separador semántico
songs.api.ts        ← excepción aceptada: punto como separador semántico

// ❌ Incorrecto — PascalCase en nombres de archivo
SongCard.tsx
LibraryPage.tsx
SongCard.module.css
```

```
// ✅ Estructura de directorios (todas en minúsculas)
src/
  api/
  components/
    song/
    stems/
    mix/
  hooks/
  layouts/
  pages/
    auth/
    library/
    create/
  router/
  store/
  types/
```

---

### 1.2 Documentación y JSDoc

Usar JSDoc (`/** ... */`) para documentar componentes, hooks y funciones de API exportadas. Los comentarios de una línea usan `//` con mayúscula inicial y punto final.

#### Componentes React

```typescript
/**
 * Tarjeta de canción con controles de reproducción, like y eliminación.
 * Obtiene la miniatura de forma asíncrona y cancela la petición si se desmonta.
 *
 * @param song - Datos de la canción a mostrar.
 * @param onPlay - Callback invocado al presionar reproducir.
 * @param onDelete - Callback invocado al confirmar la eliminación.
 * @param onPublish - Callback para alternar la visibilidad pública.
 */
export default function SongCard({ song, onPlay, onDelete, onPublish }: SongCardProps) {
  // Cancelamos la petición si el componente se desmonta antes de resolverse.
  let cancelled = false
  // ...
}
```

#### Custom Hooks

```typescript
/**
 * Hook de polling para el estado de un job de separación de stems.
 * Consulta el backend cada 3 segundos hasta que el job alcanza un estado final.
 *
 * @param jobId - ID del StemJob a monitorear, o null si no hay job activo.
 * @returns Estado actual, porcentaje de progreso, archivos generados y error.
 */
export function useStemJob(jobId: string | null) {
  const [status, setStatus] = useState<string | null>(null)
  return { status }
}
```

#### Funciones de API

```typescript
/**
 * Envía una petición de generación de canción al backend.
 *
 * @param payload - Parámetros de generación (descripción, letras, duración, etc.).
 * @returns ID del job de generación creado.
 */
export async function generateSong(payload: GenerateSongPayload): Promise<GenerateSongResponse> {
  const { data } = await client.post<GenerateSongResponse>(ENDPOINTS.songs.generate, payload)
  return data
}
```

#### Comentarios inline

```typescript
// ✅ Correcto — oración completa con punto
// Cancelamos la petición si el componente se desmonta antes de resolverse.
let cancelled = false

// ✅ Correcto — explica el "por qué", no el "qué"
// Reintenta con intervalo mayor ante errores de red.
if (!cancelled) setTimeout(poll, 6000)

// ❌ Incorrecto — sin mayúscula ni punto
// fetch thumbnail
// ❌ Incorrecto — comenta el "qué" (el código ya lo dice)
// set loading to true
setLoading(true)
```

---

### 1.3 Orden de Importaciones

El orden estándar en todos los archivos TypeScript del proyecto:

```typescript
// 1. React y librerías core
import { useState, useEffect, useRef, lazy, Suspense } from 'react'

// 2. Librerías de terceros
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

// 3. Módulos internos del proyecto (con alias @/ o ruta relativa)
import { useAuthStore } from '../store/auth.store'
import { ENDPOINTS } from '../api/endpoints'
import client from '../api/client'

// 4. Módulos de la misma feature / archivos locales
import SongCard from '../../components/song/song-card'
import type { LibrarySong } from '../../api/modules/songs.api'
import styles from './library-page.module.css'
```

> **Regla:** siempre una línea en blanco entre los grupos 1→2, 2→3 y 3→4.

---

### 1.4 Tipado TypeScript

#### Siempre tipar con interfaces y type aliases

```typescript
// ✅ Correcto — interfaz para props
interface SongCardProps {
  song: LibrarySong
  onPlay?: (song: LibrarySong) => void
  onDelete?: (songId: string) => void
}

// ✅ Correcto — union type descriptivo
type SortOption = 'recent' | 'oldest' | 'title'
type CoverState = 'loading' | 'loaded' | 'error'

// ✅ Correcto — genéricos en cliente HTTP
const { data } = await client.post<GenerateSongResponse>(ENDPOINTS.songs.generate, payload)
```

#### Tipos compartidos en `src/types/`

Los tipos reutilizados entre múltiples módulos viven en `src/types/index.ts`:

```typescript
// src/types/index.ts
export interface LibrarySong {
  id: string
  title: string
  description: string
  genre?: string
  audio_duration?: number
  created_at: string
  tags?: SongTag[]
  is_public?: boolean
}

export interface StemJob {
  id: string
  source_filename: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress_pct: number
  stem_files?: StemFile[]
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
```

#### Evitar `any`

```typescript
// ❌ Incorrecto
const handleError = (err: any) => { ... }

// ✅ Correcto — tipar la forma del error
const handleError = (err: unknown) => {
  const msg = err instanceof Error ? err.message : 'Error desconocido.'
  setError(msg)
}

// ✅ Correcto — tipo específico de respuesta axios
} catch (err: unknown) {
  const msg = (err as { response?: { data?: { detail?: string } } })
    ?.response?.data?.detail ?? 'Error al procesar.'
  setErrorMsg(msg)
}
```

#### Configuración TypeScript (`tsconfig.app.json`)

```json
{
  "compilerOptions": {
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": { "@/*": ["src/*"] }
  }
}
```

---

### 1.5 Estructura de Archivos y Carpetas

```
gm_frontend/
  src/
    api/
      client.ts               ← instancia axios centralizada con interceptores JWT
      endpoints.ts            ← constantes de todas las rutas API
      modules/
        songs.api.ts          ← funciones y tipos de canciones
        stems.api.ts
        mix.api.ts
        playlists.api.ts
        community.api.ts
        notifications.api.ts
        recommendations.api.ts
    components/
      song/
        song-card.tsx
        song-card.module.css
        lyrics-view.tsx
        lyrics-view.module.css
      stems/
        audio-uploader.tsx
        stem-progress.tsx
        stem-result-card.tsx
      mix/
        clip-card.tsx
        clip-timeline.tsx
        add-clip-modal.tsx
    hooks/
      use-stem-job.ts         ← polling de jobs de stems
      use-mix-export.ts       ← polling de exportaciones de mix
    layouts/
      app-layout.tsx          ← layout principal (sidebar + header)
      auth-layout.tsx
      admin-layout.tsx
      upgrade-modal.tsx
    pages/
      auth/
        login-page.tsx
        register-page.tsx
      library/
        library-page.tsx
        library-page.module.css
      create/
        create-page.tsx
      stems/
        stems-page.tsx
      mix/
        mix-page.tsx
        mix-editor-page.tsx
      playlists/
        playlists-page.tsx
        playlist-detail-page.tsx
      recommendations/
        for-you-page.tsx
      cliente/
        cliente-profile-page.tsx
        payments-page.tsx
        community-page.tsx
      admin/
        dashboard-page.tsx
        planes-page.tsx
        roles-page.tsx
        users-admin-page.tsx
        reports-admin-page.tsx
        admin-profile-page.tsx
    router/
      index.tsx               ← definición de rutas con lazy loading
      private-route.tsx       ← guard de autenticación
      admin-route.tsx         ← guard de rol admin
    store/
      auth.store.ts           ← estado global de autenticación (Zustand)
    types/
      index.ts                ← tipos compartidos entre módulos
```

---

### 1.6 Componentes React

#### Estructura estándar de un componente

```typescript
// 1. Importaciones (ver orden en §1.3)
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getLibrary } from '../../api/modules/songs.api'
import type { LibrarySong } from '../../api/modules/songs.api'
import SongCard from '../../components/song/song-card'
import styles from './library-page.module.css'

// 2. Types y interfaces locales al componente
type SortOption = 'recent' | 'oldest' | 'title'

// 3. Componente — default export, nombre en UpperCamelCase
/**
 * Página de biblioteca del usuario.
 * Lista las canciones generadas con búsqueda, ordenamiento y reproductor integrado.
 */
export default function LibraryPage() {
  // 4. Hooks de estado (todos agrupados al inicio)
  const [songs, setSongs] = useState<LibrarySong[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  // 5. Efectos
  useEffect(() => {
    setLoading(true)
    getLibrary()
      .then((data) => setSongs(data))
      .catch(() => setError('No se pudo cargar tu biblioteca. Intenta de nuevo.'))
      .finally(() => setLoading(false))
  }, [])

  // 6. Handlers (prefijo "handle")
  async function handleDelete(songId: string) {
    try {
      await deleteSong(songId)
      setSongs((prev) => prev.filter((s) => s.id !== songId))
    } catch {
      alert('No se pudo eliminar la canción.')
    }
  }

  // 7. Valores derivados
  const filtered = songs.filter((s) =>
    s.title?.toLowerCase().includes(search.toLowerCase())
  )

  // 8. Renders condicionales (loading, error, empty) antes del return principal
  if (loading) {
    return <div className={styles.page}>...</div>
  }

  // 9. JSX principal
  return (
    <div className={styles.page}>
      {filtered.map((song) => (
        <SongCard key={song.id} song={song} onDelete={handleDelete} />
      ))}
    </div>
  )
}
```

#### Reglas de componentes

```typescript
// ✅ Usar llaves SIEMPRE en bloques condicionales
if (loading) {
  return <Spinner />
}

// ❌ Nunca omitir llaves
if (loading) return <Spinner />

// ✅ Keys únicas en listas — usar el ID del objeto, nunca el índice
{songs.map((song) => (
  <SongCard key={song.id} song={song} />
))}

// ❌ Nunca usar el índice como key en listas dinámicas
{songs.map((song, i) => (
  <SongCard key={i} song={song} />
))}

// ✅ Cleanup en useEffect para evitar memory leaks
useEffect(() => {
  let cancelled = false
  async function fetchData() {
    const url = await getSongThumbnailUrl(song.id)
    if (!cancelled) setThumbnailUrl(url)
  }
  fetchData()
  return () => { cancelled = true }
}, [song.id])
```

---

### 1.7 Custom Hooks

Extraer lógica reutilizable o asíncrona compleja a hooks propios:

```typescript
// src/hooks/use-stem-job.ts

/**
 * Hook de polling para el estado de un job de separación de stems.
 * Consulta el backend cada 3 segundos hasta que el job alcanza un estado final.
 *
 * @param jobId - ID del StemJob a monitorear, o null si no hay job activo.
 * @returns Estado actual, porcentaje de progreso, archivos generados y error.
 */
export function useStemJob(jobId: string | null) {
  const [status, setStatus] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [stemFiles, setStemFiles] = useState<StemFile[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    let cancelled = false

    const poll = async () => {
      try {
        const data = await getStemJobStatus(jobId)
        if (cancelled) return
        setStatus(data.status)
        setProgress(data.progress_pct)
        if (!['completed', 'failed'].includes(data.status)) {
          setTimeout(poll, 3000)
        }
      } catch {
        // Reintenta con intervalo mayor ante errores de red.
        if (!cancelled) setTimeout(poll, 6000)
      }
    }

    poll()
    return () => { cancelled = true }
  }, [jobId])

  return { status, progress, stemFiles, error }
}
```

---

### 1.8 Gestión de Estado (Zustand)

```typescript
// src/store/auth.store.ts

/** Datos del usuario autenticado persistidos en localStorage. */
export interface AuthUser {
  id: string
  email: string
  full_name: string
  credit_balance: number
  role: string
}

/** Estado global de autenticación gestionado por Zustand. */
interface AuthState {
  user: AuthUser | null
  accessToken: string | null
  refreshToken: string | null
  /**
   * Almacena los tokens tras un login exitoso.
   * @param access - Token de acceso JWT.
   * @param refresh - Token de refresco JWT.
   */
  setTokens: (access: string, refresh: string) => void
  setUser: (user: AuthUser) => void
  logout: () => void
}

/**
 * Store global de autenticación con persistencia en localStorage.
 * Persiste bajo la clave 'auth-storage'.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setUser: (user) => set({ user }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    { name: 'auth-storage' }
  )
)
```

---

### 1.9 Capa de API

Toda comunicación HTTP pasa por el cliente centralizado. **Nunca** usar `fetch` o `axios` directamente en componentes.

```typescript
// src/api/client.ts

/**
 * Instancia centralizada de Axios configurada con la URL base de la API.
 * Todos los módulos de API deben usar este cliente.
 */
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api',
  headers: { 'Content-Type': 'application/json' },
})

// Adjunta el token JWT Bearer en cada petición saliente.
client.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState()
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})
```

```typescript
// src/api/endpoints.ts — centralizar TODAS las URLs
export const ENDPOINTS = {
  auth: {
    login: '/auth/login/',
    register: '/auth/register/',
    me: '/auth/me/',
    refresh: '/auth/refresh/',
  },
  songs: {
    generate: '/songs/generate/',
    library: '/songs/library/',
    detail: (id: string) => `/songs/${id}/`,
    playUrl: (id: string) => `/songs/${id}/play-url/`,
  },
  stems: {
    upload: '/stems/upload/',
    status: (id: string) => `/stems/jobs/${id}/`,
  },
}
```

```typescript
// src/api/modules/songs.api.ts — una función por operación, siempre tipada

/**
 * Obtiene la lista de canciones de la biblioteca del usuario autenticado.
 * @returns Array de canciones ordenadas por fecha de creación descendente.
 */
export async function getLibrary(): Promise<LibrarySong[]> {
  const { data } = await client.get<LibrarySong[]>(ENDPOINTS.songs.library)
  return data
}

/**
 * Envía una petición de generación de canción al backend.
 * @param payload - Parámetros de generación.
 * @returns ID del job de generación creado.
 */
export async function generateSong(payload: GenerateSongPayload): Promise<GenerateSongResponse> {
  const { data } = await client.post<GenerateSongResponse>(ENDPOINTS.songs.generate, payload)
  return data
}
```

---

### 1.10 Routing y Lazy Loading

Todas las páginas se cargan de forma diferida (`React.lazy`) para reducir el bundle inicial:

```typescript
// src/router/index.tsx
import { lazy, Suspense } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'

// Lazy import — cada página es un chunk separado
const LibraryPage = lazy(() => import('../pages/library/library-page'))
const CreatePage = lazy(() => import('../pages/create/create-page'))
const StemsPage = lazy(() => import('../pages/stems/stems-page'))

// Fallback mientras carga el chunk
function PageLoader() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      Cargando...
    </div>
  )
}

function withSuspense(element: React.ReactElement) {
  return <Suspense fallback={<PageLoader />}>{element}</Suspense>
}

export const router = createBrowserRouter([
  {
    element: <PrivateRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/library', element: withSuspense(<LibraryPage />) },
          { path: '/create',  element: withSuspense(<CreatePage />) },
        ],
      },
    ],
  },
])
```

---

### 1.11 Estilos y CSS

El proyecto usa **CSS Modules** con variables CSS globales para el sistema de diseño.

```css
/* src/index.css — tokens de diseño globales */
:root {
  --color-primary:    #A855F7;
  --color-primary-light: #C084FC;
  --bg-night:         #000000;
  --bg-surface:       #121212;
  --bg-card:          #181818;
  --bg-card-hover:    #282828;
  --text-base:        #FFFFFF;
  --text-muted:       #B3B3B3;
  --text-subdued:     #6b7280;
  --border:           #2a2a2a;
}
```

```css
/* src/components/song/song-card.module.css — estilos encapsulados por componente */
.card {
  background: var(--bg-card);
  border-radius: 8px;
  overflow: hidden;
  transition: background 0.15s;
}

.card:hover {
  background: var(--bg-card-hover);
}
```

```typescript
// Uso en el componente — importar el módulo CSS
import styles from './song-card.module.css'

export default function SongCard() {
  return <article className={styles.card}>...</article>
}
```

**Reglas:**
- Siempre usar variables CSS (`var(--color-primary)`) en lugar de valores hardcodeados.
- Los estilos inline solo para valores dinámicos calculados en runtime.
- Un archivo `.module.css` por componente.

---

### 1.12 Manejo de Errores

```typescript
// ✅ Handlers con try-catch específico
async function handleDelete(songId: string) {
  try {
    await deleteSong(songId)
    setSongs((prev) => prev.filter((s) => s.id !== songId))
  } catch {
    alert('No se pudo eliminar la canción. Intenta de nuevo.')
  }
}

// ✅ Estados de error en UI
const [error, setError] = useState<string | null>(null)

if (error) {
  return (
    <div className={styles.errorBanner}>
      {error}
    </div>
  )
}

// ✅ Tipado de errores de axios
} catch (err: unknown) {
  const msg = (err as { response?: { data?: { detail?: string } } })
    ?.response?.data?.detail ?? 'Error desconocido.'
  setError(msg)
}
```

---

## 2. Backend — Python / Django

### 2.1 Convención de Nombres

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Clases (modelos, vistas, serializers) | PascalCase | `Song`, `GenerateView`, `LoginSerializer` |
| Excepciones | PascalCase + sufijo `Error` | `InsufficientCreditsError`, `FileTooLargeError` |
| Funciones y métodos | snake_case | `request_generation`, `check_balance` |
| Variables | snake_case | `credit_balance`, `source_filename` |
| Constantes de módulo | SCREAMING_SNAKE_CASE | `BPM_RANGES`, `FINAL_STATES` |
| Constantes de clase | SCREAMING_SNAKE_CASE | `STATUS_CHOICES`, `STEM_TYPES` |
| Archivos Python | snake_case | `generation_service.py`, `modal_client.py` |
| Apps Django | lowercase | `songs`, `users`, `stems`, `credits` |

```python
# ✅ Correcto
class Song(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]
    title = models.CharField(max_length=200)
    credit_balance = models.IntegerField(default=0)

# ✅ Correcto
def request_generation(user, *, title: str, description: str = '') -> 'GenerationJob':
    ...

# ❌ Incorrecto — camelCase en Python
def requestGeneration(user, title):
    ...
```

---

### 2.2 Documentación y Docstrings

Usar Google Style para todos los docstrings. Las clases llevan docstring de clase y las funciones llevan docstring con `Args`, `Returns` y `Raises`.

#### Clases de modelos

```python
class Song(BaseModel):
    """
    Canción generada por el sistema.

    Máquina de estados: draft → queued → processing → ready | failed | no_credits.
    El campo deleted_at implementa soft delete — nunca se elimina físicamente.
    """
    STATUS_CHOICES = [('draft', 'Draft'), ('ready', 'Ready'), ('failed', 'Failed')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
```

#### Funciones y servicios

```python
def request_generation(
    user,
    *,
    title: str,
    description: str = '',
    audio_duration: int = 30,
) -> 'GenerationJob':
    """
    Punto de entrada para generar una canción.

    Valida créditos → predice parámetros con ML → crea Song + Job → encola tarea Celery.

    Args:
        user: Usuario autenticado que realiza la solicitud.
        title: Título de la canción a generar.
        description: Descripción en lenguaje natural de la música deseada.
        audio_duration: Duración en segundos (por defecto 30).

    Returns:
        GenerationJob con estado 'queued' listo para procesamiento asíncrono.

    Raises:
        InsufficientCreditsError: Si el usuario no tiene créditos suficientes.
    """
    from apps.credits.services.credit_service import check_balance

    if not check_balance(user, required=1):
        raise InsufficientCreditsError('Sin créditos disponibles.')
    # ...
```

#### Vistas

```python
class RegisterView(APIView):
    """
    Endpoint de registro de nuevos usuarios.

    POST /api/users/register/
    Crea un usuario con rol por defecto y retorna tokens JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
```

#### Comentarios inline

```python
# ✅ Correcto — oración completa, explica el "por qué"
# Importamos aquí para evitar dependencias circulares entre apps.
from apps.credits.services.credit_service import check_balance

# ✅ Correcto — explica una decisión no obvia
# Timeout de 600s: ACE-Step puede tardar entre 5 y 10 minutos.
response = requests.post(endpoint_url, json=body, timeout=600)

# ❌ Incorrecto — comenta el "qué"
# get user
user = request.user
```

---

### 2.3 Type Hints

Todas las funciones de servicios, ML y utilidades llevan anotaciones de tipo (PEP 484).

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from apps.users.models import User

# ✅ Correcto — type hints completos
def create_user(email: str, password: str, full_name: str) -> 'User':
    """Crea un nuevo usuario con rol por defecto asignado."""
    user = User.objects.create_user(
        email=email, password=password, full_name=full_name
    )
    assign_default_role(user)
    return user

def check_balance(user: 'User', required: int = 1) -> bool:
    """Verifica si el usuario tiene suficientes créditos."""
    return user.credit_balance >= required

def call_modal_endpoint(endpoint_url: str, body: dict[str, Any]) -> dict[str, Any]:
    """Llama a uno de los endpoints del servidor de generación en Modal."""
    response = requests.post(endpoint_url, json=body, timeout=600)
    if not response.ok:
        raise ModalGenerationError(f'Modal {response.status_code}: {response.text}')
    return response.json()

# ❌ Incorrecto — sin type hints
def create_user(email, password, full_name):
    ...
```

---

### 2.4 Estructura de Apps Django

Cada app sigue la misma estructura interna:

```
apps/
  <nombre_app>/
    __init__.py
    admin.py          ← registro en panel de administración
    apps.py           ← configuración de la app
    models.py         ← modelos de base de datos
    serializers.py    ← serializers DRF (validación de entrada/salida)
    views.py          ← vistas (solo orquestación, sin lógica de negocio)
    urls.py           ← rutas de la app
    services/
      __init__.py
      <nombre>_service.py   ← lógica de negocio
    tasks.py          ← tareas Celery (si aplica)
    tests.py          ← tests unitarios e integración
    migrations/
```

> **Regla de oro:** Las vistas **no** contienen lógica de negocio. Las vistas llaman a servicios. Los servicios contienen toda la lógica.

---

### 2.5 Modelos

```python
# apps/core/models.py — BaseModel compartido por todas las apps

class BaseModel(models.Model):
    """Modelo base con UUID, timestamps y soft delete para todas las entidades."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        """Marca el registro como eliminado sin borrarlo físicamente."""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self) -> bool:
        """Retorna True si el registro ha sido eliminado lógicamente."""
        return self.deleted_at is not None
```

```python
# ✅ Convenciones de modelos
class StemJob(BaseModel):
    """Job de separación de stems de audio con Demucs."""

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # ForeignKey siempre con related_name descriptivo en plural
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stem_jobs',
    )
    source_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress_pct = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
```

---

### 2.6 Vistas (Views)

```python
# ✅ Vistas delgadas — solo orquestación
class GenerateView(APIView):
    """
    Inicia la generación de una canción.

    POST /api/songs/generate/
    Requiere autenticación JWT y al menos 1 crédito disponible.
    Retorna 202 Accepted con el job_id para polling de estado.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateSongSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            job = request_generation(request.user, **serializer.validated_data)
        except InsufficientCreditsError as e:
            return Response({'detail': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)

        return Response({'job_id': str(job.id)}, status=status.HTTP_202_ACCEPTED)
```

---

### 2.7 Serializers

```python
class LoginSerializer(serializers.Serializer):
    """Serializer de autenticación que valida credenciales y retorna el usuario."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data: dict) -> dict:
        """
        Valida las credenciales contra la base de datos.

        Args:
            data: Diccionario con email y password.

        Returns:
            El mismo diccionario con el objeto user agregado.

        Raises:
            ValidationError: Si las credenciales son inválidas o la cuenta está inactiva.
        """
        user = authenticate(email=data['email'], password=data['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError('Credenciales inválidas.')
        data['user'] = user
        return data
```

---

### 2.8 Servicios (Services)

```python
# apps/credits/services/credit_service.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.users.models import User

def check_balance(user: 'User', required: int = 1) -> bool:
    """
    Verifica si el usuario tiene suficientes créditos para una operación.

    Args:
        user: Usuario a verificar.
        required: Cantidad mínima de créditos necesarios (por defecto 1).

    Returns:
        True si el usuario tiene suficientes créditos, False en caso contrario.
    """
    return user.credit_balance >= required


def deduct_credits(user: 'User', amount: int, description: str) -> None:
    """
    Deduce créditos del balance del usuario y registra la transacción.

    Args:
        user: Usuario al que se le deducen los créditos.
        amount: Cantidad de créditos a deducir.
        description: Descripción de la operación para el historial.

    Raises:
        InsufficientCreditsError: Si el balance resultante sería negativo.
    """
    if user.credit_balance < amount:
        raise InsufficientCreditsError('Sin créditos suficientes.')
    user.credit_balance -= amount
    user.save(update_fields=['credit_balance'])
```

---

### 2.9 Tareas Celery

```python
# apps/songs/tasks.py

from workers.celery import app

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_generation_job(self, job_id: str) -> None:
    """
    Procesa de forma asíncrona un job de generación de canción.

    Args:
        job_id: UUID del GenerationJob a procesar.
    """
    from apps.songs.models import GenerationJob
    from apps.songs.services.generation_service import execute_generation

    try:
        job = GenerationJob.objects.get(id=job_id)
        execute_generation(job)
    except Exception as exc:
        # Reintenta hasta 3 veces con backoff exponencial.
        raise self.retry(exc=exc)
```

---

### 2.10 Manejo de Excepciones

#### Definición de excepciones de dominio

```python
# apps/core/exceptions.py

class InsufficientCreditsError(Exception):
    """El usuario no tiene créditos suficientes para la operación solicitada."""

class FileTooLargeError(Exception):
    """El archivo supera el tamaño máximo permitido."""

class ModalGenerationError(Exception):
    """Error en la comunicación con el servidor de generación de audio en Modal."""
```

#### Uso en servicios y vistas

```python
# ✅ Servicios lanzan excepciones tipadas
def request_stem_separation(user, file, filename: str) -> 'StemJob':
    if not check_balance(user, required=2):
        raise InsufficientCreditsError('Se requieren 2 créditos para separar stems.')
    if file.size > 50 * 1024 * 1024:
        raise FileTooLargeError('El archivo supera el límite de 50 MB.')
    # ...

# ✅ Vistas capturan excepciones de dominio específicas
class UploadAndSeparateView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        try:
            job = request_stem_separation(request.user, file, file.name)
            return Response({'job_id': str(job.id)}, status=status.HTTP_201_CREATED)
        except FileTooLargeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientCreditsError as e:
            return Response({'error': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)

# ❌ Nunca capturar Exception genérica en vistas
except Exception as e:
    return Response({'error': str(e)}, status=500)
```

---

### 2.11 Seguridad y Configuración

```python
# ✅ Todas las credenciales en variables de entorno (.env)
import os
SECRET_KEY = os.environ['SECRET_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']

# ✅ .env.example con placeholders (nunca valores reales)
# SECRET_KEY=cambiar-esto-en-produccion
# OPENAI_API_KEY=
# STRIPE_SECRET_KEY=

# ✅ .gitignore incluye .env
.env
*.env

# ✅ DEBUG=False en producción
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ✅ Todos los endpoints protegidos con IsAuthenticated
class SongLibraryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    # ...
```

---

## 3. Herramientas y Configuración

### 3.1 Frontend

#### `.prettierrc`

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

#### `eslint.config.js` — reglas activas

```javascript
rules: {
  // No permitir prefijo I en interfaces (interface IUser → interface User)
  '@typescript-eslint/naming-convention': [
    'error',
    { selector: 'interface', format: ['PascalCase'], custom: { regex: '^I[A-Z]', match: false } },
    { selector: 'typeAlias', format: ['PascalCase'] },
    { selector: 'variable', format: ['camelCase', 'PascalCase', 'UPPER_CASE'] },
  ],
  // Advertir ante uso de any
  '@typescript-eslint/no-explicit-any': 'warn',
  // Siempre usar llaves
  'curly': ['error', 'all'],
  // Solo console.warn y console.error en producción
  'no-console': ['warn', { allow: ['warn', 'error'] }],
}
```

#### `package.json` — scripts disponibles

```json
{
  "scripts": {
    "dev":          "vite",
    "build":        "tsc -b && vite build",
    "lint":         "eslint .",
    "lint:fix":     "eslint . --fix",
    "format":       "prettier --write \"src/**/*.{ts,tsx,css,json}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,css,json}\"",
    "preview":      "vite preview"
  }
}
```

---

### 3.2 Backend

#### `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["N806", "N812"]

[tool.ruff.isort]
known-first-party = ["apps", "config", "ml", "workers"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
strict = false
ignore_missing_imports = true
check_untyped_defs = true

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py", "*_test.py"]
addopts = "-v --tb=short"
```

#### Instalar herramientas de desarrollo

```bash
# En el entorno virtual del backend
pip install ruff black mypy pytest pytest-django pre-commit
```

---

### 3.3 Pre-commit Hooks

`pre-commit` automatiza el formato y linting antes de cada commit. Requiere Python instalado.

#### Instalación (una sola vez por máquina)

```bash
pip install pre-commit
```

#### Activar en cada repositorio

```bash
# Dentro de gm_backend/
cd gm_backend
pre-commit install

# Dentro de gm_frontend/
cd gm_frontend
pre-commit install
```

#### `gm_backend/.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
```

#### `gm_frontend/.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: prettier
        name: Prettier
        entry: npx prettier --write
        language: node
        files: \.(ts|tsx|css|json)$

      - id: eslint
        name: ESLint
        entry: npx eslint --fix
        language: node
        files: \.(ts|tsx)$
        pass_filenames: false
```

#### Ejecutar manualmente sobre todos los archivos

```bash
pre-commit run --all-files
```

---

## 4. Referencias

| Estándar | Sección aplicada |
|----------|-----------------|
| Angular Style Guide (Google) | Estructura de carpetas, convención de nombres de archivos |
| Microsoft TypeScript Coding Guidelines | UpperCamelCase / lowerCamelCase, sin prefijo I |
| ISO/IEC 25010:2011 | Mantenibilidad, modularidad, analizabilidad |
| Clean Code — Robert C. Martin | Nombres descriptivos, funciones pequeñas, SRP |
| Principios SOLID | Service layer, separación de responsabilidades, DI |
| PEP 8 (Python) | Nombres snake_case, longitud de línea, imports |
| PEP 484 (Python) | Type hints y anotaciones de tipo |
| Google Python Style Guide | Formato de docstrings (Args / Returns / Raises) |
| 12 Factor App | Configuración en variables de entorno, sin credenciales en código |
