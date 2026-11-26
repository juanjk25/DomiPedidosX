# Sprint 1 — entrega de Emanuel

**Alcance:** A4, A6, B4, B5, B6 y B8. Cambios preparados para revisar en tu rama; no se modificó GitHub ni la base compartida. Base: commit `10ee1d0` del repositorio, confirmado sin cambios al preparar esta versión.

## 1. Qué cambió y por qué

| Historia | Resultado |
|---|---|
| **A4 · Iniciar sesión** | Usa `/api/auth/login/`, señala campos vacíos, muestra errores genéricos y abre la sección del rol. Se conserva `/auth/token/` para compatibilidad. |
| **A6 · Recuperar contraseña** | Solicita correo, muestra confirmación y permite establecer una nueva contraseña con el enlace del backend existente. |
| **B4 · Gestionar menú** | Lista productos por sede, permite crear/editar/desactivar y previsualizar el menú del cliente. |
| **B5 · Crear productos** | Guarda nombre, precio, imagen **por URL**, preparación en minutos, categoría y sede. Valida obligatorios. |
| **B6 · Editar productos** | Precarga el formulario y guarda los cambios en BD. Una edición inválida conserva los datos anteriores. |
| **B8 · Deshabilitar productos** | Pide confirmación, cambia `activo` a `false` y lo oculta al cliente sin borrar el registro. |

**Soporte de backend necesario:** se añadieron los campos y servicios que faltaban para guardar productos; categorías con descripción y sede, con nombre único por sede; y validaciones para impedir usar categorías o productos de otra sede. Se corrigió la ruta duplicada del login y el uso de `is_staff` como permiso de administrador. Un operador no puede desactivar cuentas de personal.

El menú se actualiza al abrirlo, recuperar foco o cada **15 segundos**. Se retiraron los combos ficticios que agregaban un producto distinto al anunciado. No se implementaron las historias de inventario, promociones ni los módulos operativos de cocina/reparto: estos roles tienen una entrada de sesión básica para conectar sus módulos después.

## 2. Archivos y coordinación

Estas rutas son relativas a `frontend/src/`. El ZIP ya conserva la estructura correcta.

| Historia | Archivos nuevos principales |
|---|---|
| A4 | `pages/IniciarSesion.jsx`, `pages/InicioPersonal.jsx`, `components/AuthLayout.jsx`, `components/RegistroPanel.jsx`, `utils/session.js` |
| A6 | `pages/RecuperarContrasena.jsx`, `pages/RestablecerContrasena.jsx` |
| B4 | `pages/GestionMenu.jsx`, `utils/productos.js`, `sprint1.css` |
| B5 / B6 | `components/ProductoForm.jsx`, `components/ImagenProducto.jsx` |
| B8 | `components/ConfirmarDesactivacion.jsx` |

También cambian `App.jsx`, `api.js` y `pages/MenuPromociones.jsx`. En backend se agregan `orders/catalog_views.py`, `orders/catalog_serializers.py` y migraciones **0004–0006**, además de ajustes en modelos, permisos, rutas y configuración. El inventario completo de archivos nuevos/modificados está en [archivos_sprint1.csv](archivos_sprint1.csv).

| Compañero | Qué debe revisar al integrar |
|---|---|
| **Andrés** | Contrato de login y categorías: misma tabla `Categoria`, campos `nombre`, `descripcion`, `sede`, `activo`. La entrega aporta modelo/lectura para productos; no sustituye sus historias completas B1/B3. |
| **William David** | Relación `PerfilPersonal(usuario, rol, sede)` y orden de migraciones. Si su modelo de roles es distinto, adaptar `role_of`/`branch_of`. |
| **Juan David** | Se mantienen los endpoints de recuperación y la desactivación de cuentas. Configurar SMTP para correo real; solo admin puede cambiar cuentas del personal. |
| **Junior Asprilla** | Combinar cambios de `App.jsx` y `MenuPromociones.jsx`. `RegistroCliente.jsx` se conserva. Categorías tienen IDs persistentes y se consultan por sede. |

**Para tu rama:** usa el ZIP de cambios sobre la raíz del proyecto y combina los archivos compartidos antes del commit. No reemplaces avances de compañeros sin revisar el diff. Si ya aplicaste la entrega anterior, conserva 0004/0005 y aplica la nueva **0006**. Si el equipo tiene otras migraciones con esos números, coordinen sus dependencias antes de ejecutar `migrate`.

## 3. Probar sin Docker ni tocar Supabase

Requisitos: **Python 3.12.x**, **Node.js 24.x**, tu IDE y un navegador. Descomprime el ZIP completo en una carpeta nueva y ábrela. Desde la raíz, en PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///demo.sqlite3"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Deja esa terminal abierta. En otra terminal, desde la raíz:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Abre **http://localhost:5173** e ingresa con el superusuario local que creaste. Para probar cliente, usa el registro. Para un operador, crea un usuario activo/staff y su `PerfilPersonal` con rol `operator` y sede en **http://localhost:8000/admin/**.

Si reabres la terminal del backend, vuelve a establecer `DATABASE_URL` antes de arrancar. La base local queda en `backend/demo.sqlite3`. No contiene las cuentas de Supabase. El enlace de recuperación se imprime en la terminal mientras no configures correo real.

Con Docker ya instalado pueden conservar su flujo: configurar `.env` y ejecutar `docker compose up --build`. **Ese flujo usa la base indicada en su `.env` y aplica migraciones**, por lo que debe coordinarse con el equipo.

## 4. Verificación y pendientes de cierre

Resultados y comandos: [verificacion_sprint1.md](verificacion_sprint1.md). Contratos y decisiones de integración: [contratos_sprint1.md](contratos_sprint1.md). Solo necesitas esos documentos para revisar pruebas o resolver una integración.

Antes del merge, el equipo debe:

- Comparar las pantallas con los **mockups aprobados**: las imágenes recibidas contienen criterios, no diseños.
- Ejecutar las pruebas de navegador y comprobar la integración con PostgreSQL y el correo real. Aquí se verificaron API/componentes y migraciones con SQLite; Chromium está bloqueado por el entorno.
- Revisar los registros antiguos sin sede/imagen/preparación. Las migraciones conservan datos y no adivinan una sede para productos compartidos.
- **Rotar la contraseña de BD expuesta** en el `compose.yaml` original y actualizar los `.env` del equipo. La entrega quitó la conexión fija; no cambió la contraseña remota.

Los criterios de A4 ya están incorporados. El alcance sigue el **release plan**: algunas filas detalladas sitúan A8–A11 y B7–B10 en otros sprints; el equipo debe unificar esa numeración. Esta entrega no declara completadas las historias ajenas.
