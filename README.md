# DomiPedidosX — sprint 1 de Emanuel

Entrega de **A4, A6, B4, B5, B6 y B8**, con las dependencias necesarias para ejecutarlas. Preparada para revisar e integrar en una rama; las historias de los demás integrantes no se declaran completadas.

**Empieza por [la guía breve](docs/sprint1_emanuel.md):** cambios, archivos por historia, coordinación y pasos para probar sin Docker ni conectarte a Supabase.

Documentación de consulta:

- [Inventario exacto de archivos nuevos y modificados](docs/archivos_sprint1.csv).
- [Contratos de API, datos y migraciones](docs/contratos_sprint1.md).
- [Resultados y criterios comprobados](docs/verificacion_sprint1.md).

## Ejecutar con Docker

Si el equipo ya utiliza Docker, conserva el flujo existente. Configura `.env` a partir de `.env.example` y ejecuta:

```powershell
docker compose up --build
```

Esto aplica las migraciones a la base configurada en `.env`; coordina esa actualización con el equipo. Frontend en `http://localhost:5173`, API en `http://localhost:8000/api/`, Django Admin en `http://localhost:8000/admin/`.

La URL de conexión ya no está fija en Compose. La credencial expuesta en el archivo original debe cambiarla el propietario de la base. No se incluye `.env`, historial Git, base local ni dependencias instaladas en los ZIP.

Los documentos del plan inicial y `Database_Structure.sql` son anteriores a esta entrega; las migraciones y los contratos del sprint describen el código actualizado. Los mockups aprobados, la verificación visual y la integración con PostgreSQL/correo real siguen pendientes de aceptación por el equipo.
