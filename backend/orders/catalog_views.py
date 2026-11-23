from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from .catalog_serializers import CategorySerializer, ManagedProductSerializer, MenuProductSerializer
from .models import Categoria, Producto, Sede
from .permissions import IsOrderManager, branch_of, role_of
from .serializers import SedeSerializer


def branch_param(request):
    value = request.query_params.get("sede", request.query_params.get("branch"))
    if value is None or value == "":
        return None
    try:
        if int(value) > 0:
            return int(value)
    except (TypeError, ValueError):
        pass
    raise ValidationError({"sede": "Selecciona una sede válida."})


def public_products():
    return Producto.objects.select_related("categoria", "sede").filter(activo=True).filter(
        Q(categoria__activo=True) | Q(categoria__isnull=True)
    )


def in_branch(queryset, branch):
    # Compatibilidad con productos antiguos asociados únicamente por Inventario.
    return queryset.filter(Q(sede_id=branch) | Q(sede__isnull=True, inventarios__sede_id=branch)).distinct()


class PublicCategoryListView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    def get_queryset(self):
        qs = Categoria.objects.filter(activo=True)
        branch = branch_param(self.request)
        if branch:
            qs = qs.filter(Q(sede_id=branch) | Q(
                sede__isnull=True, productos__sede__isnull=True,
                productos__activo=True, productos__inventarios__sede_id=branch,
            )).distinct()
        return qs


class PublicProductListView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = MenuProductSerializer

    def get_queryset(self):
        qs = public_products()
        branch = branch_param(self.request)
        if branch:
            qs = in_branch(qs, branch)
        category = self.request.query_params.get("categoria")
        search = self.request.query_params.get("search", "").strip()
        if category:
            qs = qs.filter(Q(categoria__nombre=category) | Q(categoria__isnull=True, tipo_de_producto=category))
        if search:
            qs = qs.filter(nombre_producto__icontains=search)
        return qs.order_by("nombre_producto", "id_producto")


class ManagedCategoryListView(generics.ListAPIView):
    permission_classes = [IsOrderManager]
    serializer_class = CategorySerializer
    def get_queryset(self):
        qs = Categoria.objects.all()
        if role_of(self.request.user) == "operator":
            qs = qs.filter(sede_id=branch_of(self.request.user))
        branch = branch_param(self.request)
        return qs.filter(sede_id=branch) if branch else qs


class ManagedBranchListView(generics.ListAPIView):
    permission_classes = [IsOrderManager]
    serializer_class = SedeSerializer

    def get_queryset(self):
        if role_of(self.request.user) == "admin":
            return Sede.objects.all()
        return Sede.objects.filter(pk=branch_of(self.request.user))


class ManagedProductQueryset:
    permission_classes = [IsOrderManager]
    serializer_class = ManagedProductSerializer

    def get_queryset(self):
        qs = Producto.objects.select_related("categoria", "sede").all()
        if role_of(self.request.user) == "operator":
            qs = qs.filter(sede_id=branch_of(self.request.user))
        branch = branch_param(self.request)
        if branch:
            qs = qs.filter(sede_id=branch)
        return qs.order_by("nombre_producto", "id_producto")


class ManagedProductListView(ManagedProductQueryset, generics.ListCreateAPIView):
    pass


class ManagedProductDetailView(ManagedProductQueryset, generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "patch", "head", "options"]
