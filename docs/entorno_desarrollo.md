# Entorno de desarrollo DomiPedidosX

## Stack y versiones acordadas

| Componente | Versión / servicio | Configuración |
|---|---|---|
| Python | 3.12.15 | `backend/.python-version`, `Dockerfile` |
| Django | 5.2.18 | `backend/requirements.txt` |
| Django REST Framework | 3.16.1 | `backend/requirements.txt` |
| PostgreSQL | Conexión provisional del prototipo a Supabase | `DATABASE_URL` en el `.env` local; la decisión final del equipo está pendiente |
| Node.js | 24.21.0 | `frontend/.nvmrc`, etapa Node del `Dockerfile` raíz |
| React | 19.3.0 | `frontend/package.json` |
| Tailwind CSS | 4.3.3 | `frontend/package.json`, plugin en `vite.config.js` |
| Vite | 8.3.4 | `frontend/package.json` |

La tabla describe el prototipo ejecutable actual, no una decisión definitiva sobre la base de datos. El motor/proveedor y el modelo final están pendientes de acuerdo del equipo y del profesor. El `.env` contiene la URL de conexión provisional y no se sube a GitHub. `frontend/package-lock.json` debe actualizarse con `npm install` y subirse al repositorio para fijar también las dependencias indirectas.

## 1. Preparar Supabase una sola vez

1. El equipo crea o abre el proyecto compartido de Supabase.
2. En el panel de Supabase, abre **Connect** y selecciona **Session pooler**. Copia la URI de PostgreSQL que muestra el panel. Para conexiones desde Docker Desktop/Windows, el pooler de sesión suele ser la opción práctica cuando la red usa IPv4. Supabase indica usar una conexión directa para backend persistente con IPv6 y el pooler de sesión como opción para redes IPv4.
3. En VS Code, abre la carpeta raíz `DomiPedidosX` y crea el `.env` a partir de la plantilla:

```powershell
Copy-Item .env.example .env
notepad .env
```

4. Reemplaza `DATABASE_URL` por la URI copiada. Si la contraseña tiene caracteres como `@`, `#`, `/` o espacios, codifícalos para URL antes de pegarla. No envíes el `.env` por el chat del equipo ni lo subas al repositorio.

La estructura esperada es parecida a:

```text
postgresql://postgres.PROJECT_REF:CONTRASENA_CODIFICADA@HOST_DEL_POOLER:5432/postgres?sslmode=require
```

Usa el host y usuario exactos que muestra el panel de Supabase; no inventes esos valores.

## 2. Ejecutar usando Docker (misma configuración para el equipo)

Requisitos: Docker Desktop instalado y en ejecución. Desde la raíz del proyecto, con `.env` ya configurado:

```powershell
docker compose up --build
```

Direcciones locales:

- Aplicación React: `http://localhost:5173`
- API Django: `http://localhost:8000/api/`
- Administración Django: `http://localhost:8000/admin/`

Compose construye una sola imagen y ejecuta un contenedor que contiene Django y React/Vite. Al iniciar, Django aplica las migraciones en Supabase. En otra terminal abierta en la raíz se cargan los datos demo y se crea el superusuario:

```powershell
docker compose exec app python manage.py seed_demo
docker compose exec app python manage.py createsuperuser
```

El superusuario se crea una sola vez por proyecto/base de datos. Para detener los servicios, vuelve a la primera terminal y presiona **Ctrl + C**. `docker compose down` quita los contenedores; conserva los datos en Supabase.

## 3. Ejecutar desde VS Code con Python/Node instalados

Usa este modo si no vas a iniciar Docker. Abre dos terminales en VS Code.

### Backend Django

En la primera terminal:

```powershell
cd .\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Si PowerShell impide activar el entorno, en esa terminal ejecuta una sola vez para la sesión y vuelve a activar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

El archivo `.env` debe estar en la raíz del proyecto, un nivel arriba de `backend`. Las migraciones y datos demo van a Supabase, no a SQLite.

### Frontend React + Tailwind

En una segunda terminal:

```powershell
cd .\frontend
npm install
npm run dev
```

Al ejecutar `npm install` por primera vez se actualiza `package-lock.json`. Inclúyelo en el primer commit y cada vez que cambien dependencias. Abre `http://localhost:5173`.

## 4. Publicar el repositorio en GitHub

1. En GitHub, crea un repositorio `DomiPedidosX`, selecciona **Public** y no marques opciones para crear README, `.gitignore` ni licencia.
2. Antes del primer commit, desde la raíz del proyecto ejecuta `cd frontend; npm install; cd ..` para generar el lockfile.
3. Inicializa y sube el código (reemplaza `TU_USUARIO` por el usuario de GitHub):

```powershell
git init
git add .
git commit -m "chore: configuracion inicial de DomiPedidosX"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/DomiPedidosX.git
git push -u origin main
```

4. Invita a los otros cuatro integrantes desde **Settings → Collaborators**. El equipo debe crear ramas por tarea, hacer commits pequeños y revisar cambios mediante Pull Requests.

Antes de subir, verifica que `.env` no aparezca en `git status`. El repositorio público contiene plantillas, nunca secretos ni datos reales.

## Archivos principales de entorno

- `Dockerfile`: construye la imagen única con Node.js y Python.
- `start-services.mjs`: ejecuta migraciones y mantiene Django y Vite activos dentro del contenedor.
- `compose.yaml`: ejecuta un solo contenedor y publica los puertos 8000 y 5173.
- `backend/requirements.txt`: fija dependencias del backend, incluido Psycopg 3 y el parser de `DATABASE_URL`.
- `frontend/package.json` y `frontend/package-lock.json`: dependencias del frontend.
- `.env.example`: plantilla de configuración; se copia a `.env` local.
- `.gitignore`: excluye `.env`, `.venv`, `node_modules` y bases locales.

No se incluye diagrama BPMN en esta carpeta.

## Documentación oficial

- [Tailwind CSS con Vite](https://tailwindcss.com/docs/installation/using-vite)
- [Conectar a PostgreSQL en Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Soporte de PostgreSQL en Django 5.2](https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes)

