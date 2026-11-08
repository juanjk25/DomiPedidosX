from django.contrib import admin
from .models import (
    Departamento, Ciudad, Cliente, CredencialCliente, Sede, 
    Producto, Ingrediente, SedeIngrediente,
    Empleado, Cajero, Repartidor, OperadorSede, Administrador,
    Pedido, DetallePedido, Factura
)

# Registro básico de modelos en el panel de administración de Django
admin.site.register(Departamento)
admin.site.register(Ciudad)
admin.site.register(Cliente)
admin.site.register(CredencialCliente)
admin.site.register(Sede)
admin.site.register(Producto)
admin.site.register(Ingrediente)
admin.site.register(SedeIngrediente)
admin.site.register(Empleado)
admin.site.register(Cajero)
admin.site.register(Repartidor)
admin.site.register(OperadorSede)
admin.site.register(Administrador)
admin.site.register(Pedido)
admin.site.register(DetallePedido)
admin.site.register(Factura)