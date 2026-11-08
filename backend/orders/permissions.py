from rest_framework.permissions import BasePermission
from .models import CredencialCliente

def role_of(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return "admin"
    try:
        user.cliente_credencial
    except CredencialCliente.DoesNotExist:
        return "admin" if user.is_staff else None
    return "customer"

class IsStaffRole(BasePermission):
    allowed_roles = {"operator", "kitchen", "courier", "admin"}
    def has_permission(self, request, view):
        return role_of(request.user) in self.allowed_roles

class IsOrderManager(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in {"operator", "admin"}
