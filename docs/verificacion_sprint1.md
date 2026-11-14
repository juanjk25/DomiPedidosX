# Verificación — versión final del sprint 1

**Resultado: 74 pruebas aprobadas.** Se utilizó una copia local; no se accedió a la base compartida ni se enviaron correos reales.

| Comprobación ejecutada | Resultado |
|---|---|
| Backend/API/migraciones | **42 aprobadas** |
| Utilidades y cliente HTTP | **8 aprobadas** |
| Componentes React e integración de navegación | **24 aprobadas** |
| Compilación de producción (`npm run build`) | Correcta |
| Django `check` | Sin incidencias |
| `makemigrations --check --dry-run` | No hay cambios sin migración |
| Prueba adicional con configuración normal y SQLite temporal | Migraciones, demo idempotente, login bcrypt/admin, desactivación y menú público correctos |
| Suite Playwright | **9 casos preparados; ejecución pendiente**. Solo se verificó su carga con `--list` |

## Criterios de Emanuel comprobados

| HU | DoR técnico disponible | DoD funcional comprobado |
|---|---|---|
| **A4** | Contrato POST `/api/auth/login/` y dependencia A5; alias anterior preservado | Obligatorios vacíos con indicación visual y foco; error genérico; autenticación y destino por rol. Pruebas con cinco roles y cuenta inactiva |
| **A6** | Flujo A4 y endpoints A7 disponibles | Correo obligatorio, confirmación, error de conexión; enlace uid/token, coincidencia de contraseñas y cambio persistente |
| **B4** | Consulta de BD y API con estado documentadas; B5 disponible | Crear/editar/desactivar; permisos por sede; datos actualizados en API/DOM y validación de campos |
| **B5** | Formulario alineado con modelo y categorías por sede | Campos obligatorios; imagen URL, precio, preparación y categoría; producto e inventario asociados a sede |
| **B6** | Campos definidos y precargados | PATCH persistente; edición inválida no altera datos; no permite categoría de otra sede |
| **B8** | Campo `activo` definido | Cancelar no modifica; confirmar desactiva sin borrar; producto excluido del menú; pruebas unitarias aprobadas |

También se comprobaron migraciones desde 0003 y 0005, separación de categorías por sede sin perder productos, nombres repetibles en sedes diferentes pero no en la misma, preservación de categorías inactivas, restricciones de personal y rechazo de pedidos con productos retirados o de otra sede. Una prueba usa el hash bcrypt real del proyecto; el resto utiliza el hash rápido del entorno aislado.

## Qué no certifican estas pruebas

- **Mockups:** se recibieron los criterios oficiales de A4, pero no los diseños aprobados. La coincidencia visual de A4/A6/B4 y la aprobación previa de B5 siguen pendientes. No se declara completo el DoR/DoD formal por pasar pruebas.
- **Navegador real:** en el intento anterior Chromium no arrancó por restricciones de sockets y se rechazó la elevación de permisos. El navegador remoto tampoco alcanzó el servidor local. No se repitió ni se eludió ese bloqueo. Los nueve escenarios de esta versión quedan para el equipo.
- **Diseño y dispositivos:** jsdom comprueba comportamiento del DOM, no apariencia, medidas, foco nativo del diálogo ni vista móvil. No hay evidencia visual aprobada.
- **Sincronización entre dispositivos:** el código consulta cada 15 segundos y al recuperar foco; el escenario con dos sesiones reales está incluido en Playwright, pendiente de ejecución.
- **Entorno del equipo:** falta verificar PostgreSQL/Supabase, migraciones de otras ramas, SMTP y entrega efectiva del correo. La prueba con configuración normal también usó SQLite local.
- **Historias ajenas:** los bloques A y B se usaron para alinear dependencias; no se certificaron sus DoD completos. Cocina/reparto tienen una entrada de sesión básica, no sus módulos operativos finales.

## Reproducir

Desde `backend`, después de instalar sus dependencias:

```powershell
.\.venv\Scripts\python.exe manage.py test orders.tests --settings=config.test_settings
.\.venv\Scripts\python.exe manage.py check --settings=config.test_settings
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings
```

Desde `frontend`, después de `npm.cmd ci`:

```powershell
npm.cmd test
npm.cmd run test:components
npm.cmd run build
```

Para Playwright, seguir el bloque al final de `contratos_sprint1.md`; la suite usa sus propios servidores y datos efímeros. `test_settings` nunca conecta a la base compartida.

**Aceptación breve del equipo:** iniciar sesión → crear producto → recargar → editar → ver cambio como cliente → cancelar y confirmar desactivación → comprobar que desaparece; probar otra sede y recuperación por correo; contrastar escritorio/móvil con el mockup.
