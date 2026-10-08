# DomiPedidosX — plan inicial del proyecto

**Curso:** Desarrollo de Software I, 2026-II  
**Versión:** borrador inicial para ajustar con el equipo y el profesor  
**Fuente de requisitos:** especificación del proyecto adjunta (9 páginas)

## 1. Objetivo y alcance

Construir una aplicación web para que clientes consulten el menú, hagan pedidos y sigan su estado, y para que el personal de una sede administre el menú, prepare pedidos y coordine entregas. El sistema tendrá varias sedes y aplicará reglas de inventario, cobertura y capacidad de forma incremental.

El **PMV** cubre acceso por roles, sedes y menú, carrito, pedidos, tablero de cocina, seguimiento básico y un panel administrativo sencillo. La **versión mejorada** agrega reglas operativas, notificaciones, promociones, reportes, pruebas y despliegue.

## 2. Supuestos que debe validar el equipo

- El equipo definió este stack: **React + Tailwind CSS** para el frontend, **Django/Python + Django REST Framework** para la API y **Supabase con PostgreSQL** para la base de datos.
- El pago es simulado. No se guardarán datos reales de tarjetas.
- El PMV usará actualización periódica de la vista para el seguimiento; WebSockets y mapa son mejoras si el tiempo alcanza.
- La cobertura se calculará inicialmente con zonas configuradas de forma sencilla (por ejemplo, barrios o radios); polígonos/mapas quedan sujetos al tiempo y al curso.
- Las cuentas de demostración y los datos semilla serán ficticios.

## 3. Product Backlog inicial

Ordenado por prioridad y dependencias. La estimación en puntos es preliminar: el equipo debe revisarla mediante Planning Poker. **P0** es necesario para el PMV; **P1** completa reglas y operación; **P2** aporta mejoras de la segunda entrega.

| ID | Prioridad | Historia de usuario | Puntos | Sprint | Criterios de aceptación resumidos |
|---|---|---|---:|---|---|
| DPX-01 | P0 | Como usuario, quiero iniciar y cerrar sesión según mi rol para acceder solo a las funciones autorizadas. | 5 | 1 | Credenciales válidas abren sesión; inválidas muestran error; rutas y acciones restringidas por rol; cerrar sesión invalida el acceso. |
| DPX-02 | P0 | Como cliente, quiero registrarme y editar mis datos para realizar pedidos con información vigente. | 5 | 1 | Valida campos obligatorios y contacto; impide duplicados según identificador/correo acordado; permite editar y consultar el perfil. |
| DPX-03 | P0 | Como cliente, quiero guardar direcciones de entrega para reutilizarlas al pedir. | 3 | 1 | Permite crear, editar y eliminar direcciones propias; exige dirección y contacto; el pedido usa una dirección seleccionada. |
| DPX-04 | P0 | Como administrador, quiero gestionar sedes y horarios para configurar dónde opera el restaurante. | 3 | 1 | Se puede crear, editar, activar/desactivar sede y definir horario; las sedes inactivas no reciben pedidos. |
| DPX-05 | P0 | Como operador, quiero administrar categorías y productos para mantener actualizado el menú. | 5 | 1 | CRUD de categorías y productos; precio no negativo; producto asociado a categoría; cambios aparecen en el menú. |
| DPX-06 | P0 | Como operador, quiero configurar disponibilidad y precio por sede para ofrecer el menú correcto en cada ubicación. | 3 | 1 | Cada sede puede activar/desactivar productos; el cliente ve solo los disponibles en la sede elegida. |
| DPX-07 | P0 | Como cliente, quiero consultar y buscar el menú por categoría para encontrar productos disponibles. | 3 | 2 | Muestra nombre, descripción y precio; filtra por categoría y texto; oculta productos no disponibles. |
| DPX-08 | P0 | Como cliente, quiero agregar, quitar y modificar productos en un carrito para preparar mi pedido. | 5 | 2 | Cambiar cantidades recalcula subtotales y total; no permite cantidad inválida; el carrito conserva sede y personalizaciones admitidas. |
| DPX-09 | P0 | Como cliente, quiero confirmar un pedido con dirección, observaciones y pago simulado para enviarlo al restaurante. | 5 | 2 | Exige dirección y método de pago; muestra resumen y total antes de confirmar; crea pedido con identificador y estado inicial; registra pago solo como simulado. |
| DPX-10 | P0 | Como operador, quiero registrar un pedido telefónico o de mostrador para atender clientes que no usan la web. | 3 | 2 | El operador selecciona/crea cliente, productos y dirección; el pedido queda asociado a su sede y aparece en cocina. |
| DPX-11 | P0 | Como personal de cocina, quiero ver la cola de pedidos y cambiar sus estados para coordinar la preparación. | 5 | 2 | Lista pedidos de la sede por estado; permite transiciones válidas recibido→preparación→listo→entregado; registra hora de cada cambio. |
| DPX-12 | P0 | Como cliente, quiero consultar el estado y mi historial para saber qué pasó con mis pedidos. | 3 | 2 | El cliente solo ve sus pedidos; el estado actual y detalle son visibles; los pedidos anteriores aparecen en historial. |
| DPX-13 | P0 | Como administrador u operador, quiero ver los pedidos del día por sede para supervisar la operación. | 3 | 2 | Filtra por sede y fecha; presenta conteo y estado; cada fila abre el detalle del pedido. |
| DPX-14 | P1 | Como operador, quiero llevar existencias por sede para evitar vender productos agotados. | 5 | 3 | Stock se actualiza por sede; pedido confirmado descuenta o reserva stock según regla acordada; stock cero oculta/bloquea el producto. |
| DPX-15 | P1 | Como administrador, quiero configurar zonas, tarifas y pedido mínimo para aplicar condiciones de entrega según cobertura. | 5 | 3 | Cada zona tiene sede, tarifa, tiempo y mínimo; pedido bajo mínimo o fuera de cobertura se rechaza con explicación. |
| DPX-16 | P1 | Como administrador, quiero fijar capacidad por sede y franja para evitar sobrecargar la cocina. | 8 | 3 | Define cupo por intervalo; los pedidos válidos consumen cupo; al llenarse bloquea la franja y sugiere alternativa disponible. |
| DPX-17 | P1 | Como operador, quiero asignar un repartidor disponible a un pedido listo para coordinar el despacho. | 5 | 3 | Solo asigna repartidores activos/disponibles de la sede; registra asignación; pedido asignado pasa a despacho/en camino según transición definida. |
| DPX-18 | P1 | Como cliente, quiero cancelar antes de que empiece la preparación para corregir un pedido enviado por error. | 3 | 3 | Solo permite cancelar en estado recibido; registra motivo y hora; libera cupo/stock reservado si aplica; cocina deja de mostrarlo como activo. |
| DPX-19 | P1 | Como usuario involucrado, quiero recibir avisos cuando cambia un pedido para actuar a tiempo. | 3 | 3 | Registra notificación de confirmación, cambio, cancelación y asignación; identifica destinatario y pedido; errores de envío no borran el pedido. |
| DPX-20 | P1 | Como operador, quiero recibir alertas de stock bajo y capacidad próxima a agotarse para anticipar problemas. | 3 | 3 | Configura mínimo de stock y umbral de capacidad; alerta se genera al cruzar umbral; no duplica alertas continuamente para el mismo evento. |
| DPX-21 | P2 | Como operador, quiero crear promociones y combos con vigencia y cupo diario para ofrecer descuentos controlados. | 5 | 4 | Define fechas, condiciones y cupo; no aplica fuera de vigencia o al agotarse; pedido muestra descuento y total desglosado. |
| DPX-22 | P2 | Como cliente, quiero ver un tiempo estimado que considere preparación y zona para planear la entrega. | 5 | 4 | Estimación combina tiempos configurados y carga; se muestra al confirmar y durante seguimiento; se actualiza con regla documentada. |
| DPX-23 | P2 | Como administrador, quiero consultar ventas y tiempos por sede, producto, zona y periodo para evaluar el servicio. | 5 | 4 | Filtros por fecha y agrupación; totales concuerdan con pedidos completados; muestra tiempos promedio y cancelaciones con periodo visible. |
| DPX-24 | P2 | Como cliente, quiero recibir notificaciones por correo de confirmaciones y cambios para mantenerme informado. | 3 | 4 | Envía mensajes a destinatarios configurados; incluye código y estado del pedido; fallos quedan registrados y no bloquean el flujo. |
| DPX-25 | P2 | Como administrador, quiero ver gráficas de ventas, ocupación y tendencias para comparar periodos y sedes. | 5 | 4 | Gráficas usan los mismos filtros del reporte; ejes y unidades son claros; estado vacío se explica. |
| DPX-26 | P2 | Como equipo de desarrollo, queremos ejecutar pruebas, documentar API e instalación y desplegar el sistema para entregar una versión reproducible. | 8 | 4 | Pruebas críticas pasan; README incluye instalación y datos demo; API tiene documentación consultable; enlace de despliegue funciona y no expone secretos. |

### Definiciones para refinar cada historia

Antes de pasar una historia a un sprint, el equipo debería confirmar: actor, valor, dependencias, reglas de negocio, criterios de aceptación comprobables, diseño/API afectada y tamaño estimado. Los criterios de la tabla son un punto de partida y deben cerrarse con el profesor como Product Owner.

## 4. Plan de trabajo por sprint

Las semanas son relativas porque el PDF no trae fechas de calendario. Cada sprint dura dos semanas según la especificación.

| Iteración | Objetivo | Alcance sugerido | Evidencia de cierre |
|---|---|---|---|
| Sprint 0 | Preparar al equipo y el producto | Acordar roles; validar este backlog; repositorio y tablero; modelo de datos; arquitectura; prototipo de flujos; entorno de desarrollo. | Backlog priorizado, plan con integrantes y fechas, ERD inicial, prototipo y README de arranque. |
| Sprint 1 | Cimientos y menú | DPX-01 a DPX-06. | Inicio de sesión por rol, mantenimiento básico y menú disponible por sede en entorno local. |
| Sprint 2 | PMV de pedidos | DPX-07 a DPX-13. | Flujo demostrable: cliente consulta, agrega al carrito, confirma; cocina actualiza; cliente consulta estado; operador ve pedidos del día. Entrega 1. |
| Sprint 3 | Reglas operativas | DPX-14 a DPX-20. | Demostración de inventario, cobertura, capacidad, cancelación, asignación y alertas. |
| Sprint 4 | Versión mejorada | DPX-21 a DPX-26. | Promociones, estimaciones, reportes, notificaciones, pruebas, despliegue y manuales. Entrega 2. |

El equipo puede mover funcionalidades entre sprints con aprobación del Product Owner. Conviene priorizar un flujo integrado funcional antes de añadir mapas o tiempo real avanzado.

## 5. Arquitectura inicial propuesta

- **Frontend:** React + Tailwind CSS, páginas para cliente, operador, cocina, repartidor y administración; componentes responsive.
- **API:** Django REST Framework; autenticación con sesiones seguras o JWT según decisión del equipo; permisos verificados en el backend.
- **Datos:** PostgreSQL en Supabase. Entidades iniciales: Usuario/Rol, Sede, Dirección, Categoría, Producto, Disponibilidad/Inventario, Zona, Pedido, ÍtemPedido, EstadoPedido, Repartidor, Asignación y Notificación.
- **Integración:** el frontend consume API REST; tareas de correo pueden empezar síncronas y pasar a cola asíncrona si hay tiempo.
- **Despliegue:** frontend y backend en servicios compatibles; secretos en variables de entorno y nunca en el repositorio.

## 6. Scrum, responsabilidades y reuniones

Completar esta tabla con las personas reales del grupo; no se inventan integrantes.

El equipo confirmó que son **5 integrantes**; faltan sus nombres y la asignación concreta de responsabilidades.

La asignación de responsabilidades debe responder a los criterios de la asignatura y a lo indicado por el profesor, no repartirse al azar. Completar la tabla con las personas reales y el criterio usado para asignar cada responsabilidad.

| Rol | Integrante(s) | Responsabilidad |
|---|---|---|
| Product Owner | Por asignar | Prioriza el backlog y valida criterios con el profesor. |
| Scrum Master | Por asignar / rotativo | Facilita ceremonias y ayuda a resolver bloqueos. |
| Desarrollo | Por asignar | Diseña, implementa, integra y documenta el incremento. |

- Planning: al inicio del sprint, máximo 2 horas.
- Daily: 15 minutos diarios o una sesión semanal de 1 hora si el curso así lo acuerda.
- Review: al cierre, demo del incremento y comentarios del profesor.
- Retrospective: al cierre, una mejora concreta para el siguiente sprint.

## 7. Definition of Done propuesta

Una historia está terminada cuando:

1. Cumple todos sus criterios de aceptación y el flujo principal se puede demostrar.
2. Respeta permisos por rol y valida datos en el backend.
3. Está integrada en la rama acordada, con commits descriptivos y revisión del equipo.
4. Incluye pruebas acordes al riesgo; no rompe los flujos ya aceptados.
5. La interfaz muestra estados de carga, éxito y error, y se puede usar en móvil.
6. Se actualizan README/API/manual cuando la historia cambia la forma de ejecutar o usar el sistema.
7. El equipo la revisa en la demo del sprint y la persona Product Owner acepta o devuelve con observaciones.

## 8. Riesgos y decisiones tempranas

- **Alcance amplio:** asegurar primero el flujo completo del PMV; mapa en vivo y optimizaciones son opcionales si amenazan la entrega.
- **Reglas ambiguas:** acordar qué significa capacidad (pedidos recibidos o en preparación), cuándo descontar stock y qué transiciones de estado se permiten.
- **Datos personales/pagos:** trabajar con datos ficticios y pago simulado; no almacenar información de tarjetas.
- **Trabajo en equipo:** registrar responsables y fechas reales en el plan, mantener ramas por funcionalidad y hacer integraciones frecuentes.
- **Despliegue:** probar temprano una versión mínima para evitar dejar configuración de nube y variables de entorno para el último sprint.

## 9. Datos que faltan para personalizar este plan

- Nombres y número de integrantes, y quién asumirá cada rol.
- Fechas reales de inicio, revisiones y entregas.
- Confirmación del stack con el profesor.
- Reglas específicas que el profesor ya haya aclarado en clase.
- URL del repositorio si el equipo ya creó uno.
