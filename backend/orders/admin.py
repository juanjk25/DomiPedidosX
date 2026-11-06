from django.contrib import admin

from .models import (
    Administrador,
    Ciudad,
    Cliente,
    Departamento,
    DetallePedido,
    Empleado,
    Factura,
    Inventario,
    Pedido,
    Producto,
    Repartidor,
    Sede,
)

admin.site.register(
    [
        Administrador,
        Ciudad,
        Cliente,
        Departamento,
        DetallePedido,
        Empleado,
        Factura,
        Inventario,
        Pedido,
        Producto,
        Repartidor,
        Sede,
    ]
)
