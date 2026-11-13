from rest_framework.permissions import BasePermission
from .models import CredencialCliente

def role_of(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return "admin"
    if hasattr(user, "perfil_trabajador"):
        rol = user.perfil_trabajador.rol
        mapeo = {
            "operador_sede": "operator",
            "cocina": "kitchen",
            "repartidor": "courier",
            "administrador": "admin",
        }
        return mapeo.get(rol, rol)
    try:
        user.cliente_credencial
        return "customer"
    except CredencialCliente.DoesNotExist:
        return "admin" if user.is_staff else None

class IsStaffRole(BasePermission):
    allowed_roles = {"operator", "kitchen", "courier", "admin"}
    def has_permission(self, request, view):
        return role_of(request.user) in self.allowed_roles

class IsOrderManager(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in {"operator", "admin"}
