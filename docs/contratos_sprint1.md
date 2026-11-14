# Contratos de integración — consultar cuando haga falta

Complemento técnico de la guía breve. Alcance: las seis HU de Emanuel y las dependencias que requieren para funcionar.

## API

Prefijo `/api`; los listados devuelven arrays sin paginación.

| Método y ruta | Entrada / salida | Acceso |
|---|---|---|
| POST `/auth/login/` | `{username,password}` → `{access,refresh,user}` | Público |
| POST `/auth/token/` | Alias compatible del login anterior | Público |
| POST `/auth/token/refresh/` | `{refresh}` → `{access}` | Público |
| GET `/me/` | Perfil con `role`, `sede`, `can_manage_menu`; dirección del cliente | Autenticado |
| POST `/auth/password-reset/` | `{email}` → confirmación genérica | Público |
| POST `/auth/password-reset/confirm/` | `{uid,token,new_password}` | Público |
| GET `/categories/?sede=1` | Categorías activas de esa sede | Público |
| GET `/products/?sede=1&categoria=Comida&search=pizza` | Productos activos; filtros combinables | Público |
| GET `/management/branches/` | Sedes autorizadas | Operador/admin |
| GET `/management/categories/` | Categorías con estado; admite `?sede=1` | Operador: solo su sede; admin: todas |
| GET/POST `/management/products/` | Listado con inactivos o creación; GET admite `?sede=1` | Operador de esa sede/admin |
| GET/PATCH `/management/products/{id}/` | Consulta/edición; `{"activo":false}` desactiva | Operador de esa sede/admin |
| PATCH `/team-members/{id}/status/` | `{is_active}`; preserva endpoint existente | Solo admin; no puede desactivarse a sí mismo |

`/auth/login` sin barra también está admitido. `branch` es alias de `sede` en filtros. `categoria` en la consulta pública es el **nombre**; en el cuerpo de un producto es el **ID**. Se conservan registro (`/auth/register/`, `/usuarios/`) y recuperación. No hay DELETE de productos.

Ejemplo de creación; sustituir IDs y URL por los reales:

```json
{
  "codigo_de_barras": "PIZZA-001",
  "nombre_producto": "Pizza margarita",
  "precio_compra": "12000.00",
  "precio_venta": "25000.00",
  "categoria": 1,
  "sede": 1,
  "imagen_url": "https://ejemplo.com/margarita.jpg",
  "tiempo_preparacion": 20,
  "activo": true
}
```

## Campos y reglas

| Dato | Regla |
|---|---|
| Nombre/código | Obligatorios; 80/30 caracteres. Código único global heredado de la BD. |
| Precio | Venta > 0; compra ≥ 0 (por defecto 0). Hasta 12 dígitos con 2 decimales. Interfaz COP. |
| Imagen | URL HTTP/HTTPS de hasta 500 caracteres. Reemplazo visual si no carga. No se añadió almacenamiento de archivos. |
| Preparación | Entero de 1 a 1440 minutos. Límite técnico, ajustable si el equipo acuerda otro. |
| Sede y categoría | Obligatorias para productos nuevos; categoría activa y de la misma sede. El operador no puede utilizar otra sede. |
| Publicación | `Producto.activo` y `Categoria.activo`. Si alguno es falso, no aparece en el menú público. |
| Categoría | `id`, `nombre`, `descripcion`, `sede`, `activo`. Nombre único dentro de la misma sede (comparación exacta). |

`tipo_de_producto` permanece como campo de salida para los filtros existentes y toma el nombre de la categoría relacionada. Los IDs de categoría son persistentes. Una creación/edición inválida no se guarda. El frontend muestra los errores del servidor y conserva el formulario.

Crear un producto crea también su fila de inventario con cantidad inicial cero. **En este sprint la publicación no depende del stock**: el bloqueo por agotados corresponde a B14. No se implementó esa regla anticipadamente. Los pedidos sí rechazan productos retirados o ajenos a la sede para evitar confirmar un carrito antiguo.

## Roles y navegación de A4

| Rol | Destino / permiso |
|---|---|
| `customer` | `/menu`, cliente |
| `operator` | `/gestion-menu`, solo sede asignada |
| `admin` | `/gestion-menu`, todas las sedes; corresponde al superusuario actual |
| `kitchen`, `courier` | `/personal`, entrada básica identificada por rol; sus módulos operativos se integran después |
| Sin perfil de rol | `/personal`, aviso de asignación pendiente; sin gestión |

Los empleados necesitan usuario activo/staff y `PerfilPersonal`. El indicador `is_staff` permite acceso potencial a Django Admin, pero **no equivale a administrador de la aplicación**. Los permisos finales se comprueban en servidor. La consulta de clientes está limitada a operador/admin; el cambio de estado de cuentas, a admin. Esto corrige una interferencia del permiso anterior `IsAdminUser`, que aceptaba cualquier staff.

El contrato de rol usa `customer` (antes el serializer declaraba `cliente`). Los compañeros deben consumir `role`/`can_manage_menu` de `/me/`; no confiar en un rol guardado manualmente en el navegador. Se mantiene el almacenamiento JWT del proyecto con renovación de access token.

## Migraciones y compatibilidad de datos

- **0004:** campos de producto, categoría y perfil de personal.
- **0005:** relaciona categorías del texto previo y asigna sede cuando hay una sola en inventario.
- **0006:** agrega descripción y sede a categorías, permite el mismo nombre en sedes distintas y relaciona cada producto con la categoría de su sede. Conserva nombres, precios y estados; no modifica 0004/0005 ya entregadas.

Si una categoría anterior se usaba en varias sedes, 0006 conserva un registro original y crea los necesarios para las otras sedes. Si queda asociada a productos sin sede, mantiene una categoría transitoria sin sede para esos registros. Las descripciones desconocidas quedan vacías; Django Admin exige completarlas y asignar sede al guardar categorías. Esta tolerancia de datos antiguos no autoriza usar categorías sin sede en productos nuevos.

Los productos compartidos entre varias sedes por inventario conservan `sede=null`; la lectura pública mantiene la relación antigua. Solo el admin los ve en gestión con “Todas las sedes”; no se permite asignarlos silenciosamente a una sede si su inventario corresponde a otra o a varias. El equipo debe decidir su separación sin perder historial. Productos antiguos sin imagen/minutos deben completarse al editar, pero pueden desactivarse directamente.

La reversión de 0006 se bloquea si existen nombres repetidos entre sedes: fusionarlos automáticamente perdería su independencia. Planificar una reversión de datos con respaldo. No ejecutar `Database_Structure.sql` para reemplazar estas migraciones; ese archivo es el esquema anterior.

## Consulta de BD — DoR B4

Ejemplo de inspección para sede 1; el acceso del cliente siempre debe pasar por la API:

```sql
SELECT id, nombre, descripcion, sede_id, activo
FROM categorias WHERE sede_id = 1 ORDER BY nombre;

SELECT p.id_producto, p.nombre_producto, p.precio_venta,
       p.imagen_url, p.tiempo_preparacion, p.activo, p.sede_id,
       c.id AS categoria_id, c.nombre, c.activo AS categoria_activa
FROM productos p
LEFT JOIN categorias c ON c.id = p.categoria_id
WHERE p.sede_id = 1
ORDER BY p.nombre_producto;
```

## Dependencias que siguen siendo del equipo

- **A1–A3/A8:** registro, georreferenciación, validaciones y perfil. Se conservan los componentes originales; esta entrega no certifica esas HU. `RegistroPanel` adapta las mismas props de `RegistroCliente`.
- **A5/A7:** contratos de autenticación y recuperación existentes. Se corrige la ruta duplicada de JWT y se agrega el alias de login requerido. A7 conserva token de una hora y validación de Django. SMTP y entrega real del correo deben verificarse con Juan David; el valor por defecto imprime el enlace en consola.
- **A9–A11:** el perfil mínimo y el permiso corregido habilitan la integración; no sustituyen su gestión de personal, auditoría ni asignación completa de roles.
- **B1–B3:** modelo de categoría y lectura por sede preparados como dependencia. Los endpoints/pantallas propios de creación, edición y desactivación de categorías deben compartir ese modelo, o acordar su adaptación. Django Admin permite preparar categorías para la demo.
- **B7/B9/B10:** la pantalla del cliente conserva filtros existentes y añade sede/actualización/imagen. `products` mantiene `{id,name,price,category_name,description}` y añade `image`.
- **B11–B16:** inventario operativo, agotados, alertas y promociones fuera del alcance de esta entrega. No se deben marcar como completados por estos cambios.

## Pruebas de navegador en el equipo

Desde `frontend`, con puertos 8000 y 5173 libres y el backend instalado:

```powershell
npx.cmd playwright install chromium
$env:DOMI_PYTHON = (Resolve-Path ..\backend\.venv\Scripts\python.exe).Path
npm.cmd run test:e2e
```

La suite inicia sus propios servidores y SQLite efímero; no reutiliza una base compartida. Hay nueve escenarios y reporte en `frontend/playwright-report/`. No usar `config.test_settings` para desplegar: tiene credenciales ficticias y hash rápido de pruebas. La guía de inicio local utiliza la configuración normal con SQLite.
