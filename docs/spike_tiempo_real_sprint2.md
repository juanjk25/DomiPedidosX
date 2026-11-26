# HU-D5a: Spike de actualización en tiempo real

**Responsable:** Juan David — back-end  
**Estado:** comparación preparada; falta acordar la decisión con el equipo.

## Objetivo

Comparar opciones para que la pantalla de cocina reciba actualizaciones de pedidos y proponer un mecanismo inicial para el proyecto.

## Comparación de alternativas

| Mecanismo | Cómo funciona | Ventajas | Costos o límites |
|---|---|---|---|
| Polling | El navegador consulta la API cada cierto intervalo, por ejemplo, cada cinco segundos. | Reutiliza la API REST y es sencillo de implementar y probar. | Puede tardar hasta el intervalo en reflejar un cambio y genera consultas aunque nada haya cambiado. |
| Server-Sent Events (SSE) | El navegador abre una conexión HTTP y el servidor le envía eventos. | Sirve para enviar novedades desde el servidor hacia la pantalla. | Requiere mantener conexiones abiertas y manejar el envío y la reconexión de eventos. |
| WebSocket | Cliente y servidor mantienen una conexión bidireccional. | Permite intercambiar información con poca demora en ambas direcciones. | Requiere manejar conexiones, autenticación y reconexiones, y puede necesitar infraestructura adicional. |

## Propuesta para discutir

Para el primer tablero de cocina se propone probar **polling cada cinco segundos** contra el endpoint:

`GET /api/pedidos/cocina/`

Es una propuesta inicial, no un acuerdo confirmado. El equipo debe decidir si cinco segundos son suficientes, cuántas pantallas esperan por sede y si más adelante se necesita SSE o WebSocket.

## Prototipo

El archivo `docs/prototipos/polling_cocina.ps1` consultará el endpoint y mostrará cuánto tarda cada respuesta. Requiere que el backend esté iniciado y un token vigente de un usuario de cocina con sede asignada.

En PowerShell, desde la raíz del proyecto:

```powershell
$env:DOMI_ACCESS_TOKEN = "PEGA_AQUI_EL_ACCESS_TOKEN"
.\docs\prototipos\polling_cocina.ps1
```

Presiona `Ctrl+C` para detenerlo. No guardes ni subas el token a GitHub.

## Pendientes para cerrar el spike

- Acordar la recomendación con el equipo.
- Confirmar con la persona responsable de HU-D3 los nombres definitivos de los estados.
- Probar el prototipo con pedidos de prueba.
- Medir la latencia en el entorno compartido antes de afirmar que cumple el objetivo de menos de 200 ms.