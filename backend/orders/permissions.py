from rest_framework.permissions import BasePermission
from .models import CredencialCliente, PerfilPersonal, PerfilTrabajador

def role_of(user):
    if not user or not user.is_authenticated or not user.is_active:
        return None
    if user.is_superuser:
        return "admin"
    if user.is_staff:
        try:
            return user.perfil_personal.rol
        except PerfilPersonal.DoesNotExist:
            try:
                role = user.perfil_trabajador.rol
            except PerfilTrabajador.DoesNotExist:
                return None
            return {
                "operador_sede": "operator",
                "cocina": "kitchen",
                "repartidor": "courier",
                "administrador": "admin",
            }.get(role, role)
    try:
        user.cliente_credencial
    except CredencialCliente.DoesNotExist:
        return None
    return "customer"

def branch_of(user):
    try:
        return user.perfil_personal.sede_id
    except (PerfilPersonal.DoesNotExist, AttributeError):
        try:
            return user.perfil_trabajador.sede_id
        except (PerfilTrabajador.DoesNotExist, AttributeError):
            return None

class IsStaffRole(BasePermission):
    allowed_roles = {"operator", "kitchen", "courier", "admin"}
    def has_permission(self, request, view):
        return role_of(request.user) in self.allowed_roles

class IsOrderManager(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in {"operator", "admin"}

class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) == "admin"
