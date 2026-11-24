from rest_framework.permissions import BasePermission
from .models import CredencialCliente, PerfilPersonal, PerfilTrabajador

ROLE_ALIASES = {
    "operador_sede": "operator",
    "cocina": "kitchen",
    "repartidor": "courier",
    "administrador": "admin",
}


def role_of(user):
    if not user or not user.is_authenticated or not user.is_active:
        return None
    if user.is_superuser:
        return "admin"
    if user.is_staff:
        raw_role = None
        try:
            raw_role = user.perfil_personal.rol
        except PerfilPersonal.DoesNotExist:
            try:
                raw_role = user.perfil_trabajador.rol
            except PerfilTrabajador.DoesNotExist:
                return None
        return ROLE_ALIASES.get(raw_role, raw_role)
    try:
        user.cliente_credencial
    except CredencialCliente.DoesNotExist:
        return None
    return "customer"


def branch_of(user):
    if not user or not user.is_authenticated:
        return None
    try:
        if user.perfil_personal.sede_id is not None:
            return user.perfil_personal.sede_id
    except (PerfilPersonal.DoesNotExist, AttributeError):
        pass
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