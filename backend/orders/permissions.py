from rest_framework.permissions import BasePermission

from .models import Administrador, CredencialCliente, Empleado


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
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return "admin"

    try:
        user.cliente_credencial
    except CredencialCliente.DoesNotExist:
        if not user.is_staff:
            return None

        email = (getattr(user, "email", "") or "").strip()

        if email and Administrador.objects.filter(
            correo_administrador__iexact=email
        ).exists():
            return "admin"

        employee = _employee_for(user)

        if employee:
            return _role_from_cargo(employee.cargo)

        # Conserva el comportamiento que ya tenía el archivo:
        # un usuario del personal sin empleado asociado se considera admin.
        return "admin"

    return "customer"


def branch_of(user):
    """Devuelve la sede asociada al empleado por su correo."""
    if not user or not user.is_authenticated or not user.is_staff:
        return None

    employee = _employee_for(user)
    return employee.sede_id if employee else None


class IsStaffRole(BasePermission):
    allowed_roles = {"operator", "kitchen", "courier", "admin"}

    def has_permission(self, request, view):
        return role_of(request.user) in self.allowed_roles


class IsOrderManager(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in {"operator", "admin"}


class IsKitchenStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if not user.is_staff:
            return False

        email = (getattr(user, "email", "") or "").strip()

        if email and Administrador.objects.filter(
            correo_administrador__iexact=email
        ).exists():
            return True

        employee = _employee_for(user)

        if not employee:
            return False

        return _role_from_cargo(employee.cargo) in {"kitchen", "admin"}