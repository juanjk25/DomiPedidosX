from rest_framework.permissions import BasePermission
from .models import CredencialCliente, CredencialEmpleado

def role_of(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return "admin"
    
    try:
        if user.cliente_credencial:
            return "cliente"
    except CredencialCliente.DoesNotExist:
        pass
        
    try:
        cred_emp = user.empleado_credencial
        if cred_emp.empleado.cargo.lower() == "operador de sede":
            return "operator"
    except CredencialEmpleado.DoesNotExist:
        pass
        
    return "admin" if user.is_staff else None

class IsStaffRole(BasePermission):
    allowed_roles = {"operator", "kitchen", "courier", "admin"}
    def has_permission(self, request, view):
        return role_of(request.user) in self.allowed_roles

class IsOrderManager(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in {"operator", "admin"}
