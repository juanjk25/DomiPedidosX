# Arquitectura preliminar

## Componentes generales

- **Frontend:** React y Tailwind CSS para la interfaz web.
- **Backend:** Python y Django REST Framework para exponer servicios mediante una API.
- **Comunicación:** la aplicación web consume la API del backend.
- **Ejecución de desarrollo:** un Dockerfile construye la imagen y Docker Compose inicia un contenedor con los dos servicios.

## Base de datos y modelo de datos — pendientes

El equipo aún no ha acordado la tecnología/proveedor definitivo de la base de datos ni el diseño lógico de los datos. Por tanto, este documento no fija un motor, un proveedor, un diagrama entidad-relación, tablas, entidades, relaciones o reglas de persistencia como decisiones aprobadas.

El código actual contiene una configuración técnica provisional para permitir ejecutar el prototipo. Esta configuración no constituye el acuerdo final del grupo. Cuando el equipo y el profesor definan la solución, se actualizarán la arquitectura, el modelo de datos, las migraciones y la documentación de ejecución.

## Otras decisiones por acordar

- Alcance funcional definitivo del PMV y criterios de aceptación.
- Reglas de negocio que dependan del diseño de datos.
- Estrategia de autenticación y permisos que se presentará como decisión del proyecto.
- Requisitos de despliegue y ambientes finales.

> Este archivo es una descripción preliminar. No sustituye el Product Backlog ni el Release Plan, que también están pendientes de definición.
