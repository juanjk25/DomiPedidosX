from rest_framework.permissions import BasePermission

from .models import (
    Administrador,
    CredencialCliente,
    Empleado,
    PerfilPersonal,
    PerfilTrabajador,
)

ROLE_ALIASES = {
    "operador_sede": "operator",
    "cocina": "kitchen",
    "repartidor": "courier",
    "administrador": "admin",
}


def _employee_for(user):
    """Busca el empleado cuyo correo coincide con el del usuario de Django."""
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return None
    return Empleado.objects.filter(correo_empleado__iexact=email).first()


def _role_from_cargo(cargo):
    """Convierte el cargo del empleado al rol que usa la API."""
    cargo = (cargo or "").strip().lower()

    if "cocin" in cargo or "chef" in cargo or "kitchen" in cargo:
        return "kitchen"
    if "repart" in cargo or "domicil" in cargo or "courier" in cargo:
        return "courier"
    if "operador" in cargo or "cajero" in cargo or "operator" in cargo:
        return "operator"
    if "admin" in cargo:
        return "admin"

    return None


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
                raw_role = None

        if raw_role:
            return ROLE_ALIASES.get(raw_role, raw_role)

        email = (getattr(user, "email", "") or "").strip()
        if email and Administrador.objects.filter(
            correo_administrador__iexact=email
        ).exists():
            return "admin"

        employee = _employee_for(user)
        if employee:
            return _role_from_cargo(employee.cargo)

        return None

    try:
        user.cliente_credencial
    except CredencialCliente.DoesNotExist:
        return None

    return "customer"


def branch_of(user):
    """Devuelve la sede asociada al usuario del personal o empleado."""
    if not user or not user.is_authenticated:
        return None

    try:
        if user.perfil_personal.sede_id is not None:
            return user.perfil_personal.sede_id
    except (PerfilPersonal.DoesNotExist, AttributeError):
        pass

    try:
        if user.perfil_trabajador.sede_id is not None:
            return user.perfil_trabajador.sede_id
    except (PerfilTrabajador.DoesNotExist, AttributeError):
        pass

    if user.is_staff:
        employee = _employee_for(user)
        return employee.sede_id if employee else None

    return None


class IsStaffRole(BasePermission):
    allowed_roles = {"operator", "kitchen", "courier", "admin"}

    def has_permission(self, request, view):
        return role_of(request.user) in self.allowed_roles


class IsOrderManager(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in {"operator", "admin"}


class IsKitchenStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in {"kitchen", "admin"}


class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) == "admin"