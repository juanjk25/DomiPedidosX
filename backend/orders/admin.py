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

from .models import Categoria, PerfilPersonal

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "sede", "activo"]
    list_filter = ["sede", "activo"]
    search_fields = ["nombre"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["sede"].required = True
        form.base_fields["descripcion"].required = True
        return form

@admin.register(PerfilPersonal)
class PerfilPersonalAdmin(admin.ModelAdmin):
    list_display = ["usuario", "rol", "sede"]
    list_filter = ["rol", "sede"]
