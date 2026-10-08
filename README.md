# DomiPedidosX

Aplicación web académica para gestionar pedidos y domicilios de un restaurante con varias sedes. Esta primera versión cubre el flujo central del PMV: el cliente se registra, consulta el menú de una sede, arma el carrito, confirma un pedido con pago simulado y ve su estado. El personal de sede puede consultar pedidos y cambiar sus estados según su rol.

## Tecnologías

- API: Django 5.2, Django REST Framework y Simple JWT.
- Web: React 19, Vite 8 y Tailwind CSS 4.
- Base de datos: PostgreSQL administrado en Supabase.

## Requisitos

Para ejecutar todo el equipo con versiones iguales, usa Docker Desktop y Compose. Si trabajas sin Docker, usa Python `3.12.15` y Node.js `24.21.0` (también anotadas en `backend/.python-version` y `frontend/.nvmrc`). Necesitas un proyecto de Supabase y su URL de conexión a PostgreSQL.

## Ejecutar con Docker (recomendado para el equipo)

1. Crea o abre el proyecto del equipo en Supabase. En **Connect**, copia la URL de **Session pooler** para el backend local.
2. Desde la raíz del proyecto, copia el archivo de ejemplo y abre `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

3. Reemplaza `DATABASE_URL` con la cadena de conexión que Supabase muestra en **Connect → Session pooler**. Codifica los caracteres especiales de la contraseña para URL (por ejemplo, `@` como `%40`). No compartas ni subas el archivo `.env`.
4. Instala y abre Docker Desktop. Desde la carpeta raíz, inicia la aplicación:

```powershell
docker compose up --build
```

La primera ejecución construye las imágenes y aplica las migraciones a Supabase automáticamente. Luego abre `http://localhost:5173`. La API queda en `http://localhost:8000/api/` y el panel administrativo en `http://localhost:8000/admin/`. Para detener ambos servicios, presiona **Ctrl + C** en esa terminal. Los datos quedan en PostgreSQL de Supabase.

Para cargar los productos de demostración, abre otra terminal en la carpeta raíz y ejecuta:

```powershell
docker compose exec backend python manage.py seed_demo
```

Para crear la cuenta que ingresa al panel administrativo:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Para volver a iniciar el proyecto después, ejecuta `docker compose up`. Para detener y quitar los contenedores usa `docker compose down`. Esto no borra los datos de Supabase.

Docker fija Python `3.12.15` y Node.js `24.21.0`. El backend instala dependencias exactas desde `backend/requirements.txt`. En la primera preparación del frontend, `npm install` actualiza y genera `frontend/package-lock.json`; inclúyanlo en Git para que todo el equipo use el mismo árbol de dependencias.

## Publicar en GitHub

1. En GitHub, crea un repositorio llamado `DomiPedidosX` con visibilidad **Public**. No marques las opciones para crear README, `.gitignore` ni licencia: esos archivos ya están en este proyecto.
2. Abre PowerShell en la carpeta raíz del proyecto y actualiza el lockfile del frontend antes del primer commit:

```powershell
cd .\frontend
npm install
cd ..
```

3. Configura el primer commit:

```powershell
git init
git add .
git commit -m "chore: configuracion inicial de DomiPedidosX"
git branch -M main
```

4. Copia la URL HTTPS del repositorio recién creado y enlázalo (reemplaza `TU_USUARIO` por tu usuario de GitHub):

```powershell
git remote add origin https://github.com/TU_USUARIO/DomiPedidosX.git
git push -u origin main
```

5. Invita a los otros cuatro integrantes desde **Settings → Collaborators**. Ellos pueden descargar el proyecto con:

```powershell
git clone https://github.com/TU_USUARIO/DomiPedidosX.git
cd DomiPedidosX
docker compose up --build
```

El `.gitignore` excluye archivos `.env`, bases SQLite locales, `node_modules` y entornos virtuales para evitar subir secretos o archivos propios de cada computador. No suban contraseñas ni claves reales al repositorio público.

## Abrir en VS Code

Abre `DomiPedidosX.code-workspace` o selecciona esta carpeta desde **File → Open Folder**. El proyecto incluye tareas de VS Code para iniciar el backend y el frontend desde **Terminal → Run Task**. Primero instala las dependencias siguiendo los pasos de abajo.

## Ejecutar en Windows

Desde la raíz del proyecto, crea el `.env` y pega la URL de Supabase como se explicó arriba. En la primera terminal entra a `backend/`:

```powershell
cd .\backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_demo
.venv\Scripts\python.exe manage.py createsuperuser
.venv\Scripts\python.exe manage.py runserver
```

La API queda en `http://127.0.0.1:8000/api/` y el panel administrativo en `http://127.0.0.1:8000/admin/`.

En otra terminal, desde la raíz del proyecto, entra a `frontend/`:

```powershell
cd .\frontend
npm install
npm run dev
```

El primer `npm install` crea/actualiza el lockfile. Abre `http://127.0.0.1:5173`. La web usa por defecto la API local. Si cambias la dirección, copia `frontend/.env.example` a `frontend/.env` y ajusta `VITE_API_URL` antes de ejecutar Vite.

## Datos de demostración y roles

- `seed_demo` crea la sede DomiPedidos Centro, dos categorías y productos ficticios.
- El registro público crea clientes. Las contraseñas deben cumplir las validaciones de Django.
- Para crear personal, inicia sesión en Django Admin con el superusuario y crea una cuenta. En su perfil asigna rol y sede. El panel administrativo queda reservado al superusuario.
- Roles iniciales: `customer`, `operator`, `kitchen`, `courier` y `admin`. El superusuario siempre obtiene permisos de administrador.
- Los pedidos descuentan existencias al confirmar. El pago se registra solo como simulado: no se guardan datos de tarjetas.

## Endpoints iniciales

| Método | Endpoint | Acceso / uso |
|---|---|---|
| POST | `/api/auth/register/` | Público; registra cliente |
| POST | `/api/auth/token/` | Público; obtiene JWT con usuario y contraseña |
| POST | `/api/auth/token/refresh/` | Público; renueva el access token |
| GET, PATCH | `/api/me/` | Usuario autenticado; consulta o edita su perfil |
| GET, POST | `/api/addresses/` | Usuario autenticado; listar o guardar dirección propia |
| GET, PATCH, DELETE | `/api/addresses/{id}/` | Usuario autenticado; consultar, editar o eliminar dirección propia |
| GET | `/api/customers/?search=texto` | Operador/admin; buscar clientes activos |
| GET | `/api/branches/` | Público; sedes activas |
| GET | `/api/categories/` | Público; categorías activas |
| GET | `/api/products/?branch=1` | Público; menú por sede; admite `category` y `search` |
| GET, POST | `/api/orders/` | Autenticado; historial visible según rol o creación de pedido |
| POST | `/api/orders/{id}/cancel/` | Cliente propietario; cancela solo antes de la preparación y devuelve existencias |
| PATCH | `/api/orders/{id}/status/` | Personal; cambia estados permitidos para su rol y sede |

Para crear un pedido, `POST /api/orders/` recibe `branch`, `delivery_address`, `payment_method`, `notes` e `items`, donde cada ítem tiene `product_id` y `quantity`. El servidor valida sede, disponibilidad y existencias; calcula subtotales, domicilio y total. El cliente crea el pedido a su nombre; operador/admin debe incluir además `customer` con el ID del cliente. El operador solo puede registrar pedidos en su sede asignada.

## Decisiones y alcance pendiente

- Django se conecta a Supabase PostgreSQL por `DATABASE_URL`; no se configura una segunda base de datos local.
- Menú, categorías y sedes se administran por Django Admin en esta primera iteración.
- La cobertura por zona, capacidad por franja, direcciones guardadas, asignación de repartidor, reportes, correos, pruebas funcionales y despliegue quedan para los siguientes sprints.
- Antes de publicar fuera de una demo académica, configura una `DJANGO_SECRET_KEY` aleatoria, `DEBUG=false`, dominios permitidos, HTTPS y un manejo de tokens adecuado para producción.

## Documentos del proyecto

El backlog, el plan inicial de sprints, la arquitectura y la Definition of Done están en `docs/plan_inicial.md` y `docs/arquitectura_y_modelo.md`. Completa nombres, fechas y acuerdos que el profesor dé en clase.
