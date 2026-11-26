from django.db.models import F, Q
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .catalog_views import branch_param
from .inventory_serializers import InventoryDisableSerializer, InventorySerializer
from .models import Inventario
from .permissions import IsOrderManager, branch_of, role_of


def parse_bool_param(request, param_name):
    value = request.query_params.get(param_name)
    if value is None or value == "":
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "si", "sí"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValidationError(
        {param_name: f"El parámetro '{param_name}' debe ser true o false."}
    )


class ManagedInventoryQueryset:
    permission_classes = [IsOrderManager]
    serializer_class = InventorySerializer

    def get_queryset(self):
        qs = Inventario.objects.select_related(
            "producto",
            "producto__categoria",
            "sede",
        ).all()

        if role_of(self.request.user) == "operator":
            sede_id = branch_of(self.request.user)
            if sede_id is None:
                raise PermissionDenied("El operador no tiene una sede asignada.")
            qs = qs.filter(sede_id=sede_id)
        else:
            branch = branch_param(self.request)
            if branch:
                qs = qs.filter(sede_id=branch)

        return qs.order_by("producto__nombre_producto", "id_inventario")


@extend_schema_view(
    get=extend_schema(
        tags=["Inventario"],
        summary="Listar inventario de la sede",
        description=(
            "Lista los registros de inventario. El operador de sede consulta "
            "únicamente su sede asignada y el administrador puede filtrar por sede."
        ),
        parameters=[
            OpenApiParameter(
                name="sede",
                type=int,
                required=False,
                description="Filtra por ID de sede (solo aplica para administrador).",
            ),
            OpenApiParameter(
                name="activo",
                type=bool,
                required=False,
                description="Filtra por estado activo (true/false).",
            ),
            OpenApiParameter(
                name="stock_bajo",
                type=bool,
                required=False,
                description="Si es true, devuelve solo registros con cantidad <= stock mínimo.",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                required=False,
                description="Busca por nombre de producto o código de barras.",
            ),
        ],
    ),
    post=extend_schema(
        tags=["Inventario"],
        summary="Crear registro de inventario",
        description=(
            "Crea un nuevo registro de inventario para un producto en la sede "
            "del operador o en la sede indicada por el administrador."
        ),
    ),
)
class ManagedInventoryListCreateView(
    ManagedInventoryQueryset, generics.ListCreateAPIView
):
    def get_queryset(self):
        qs = super().get_queryset()

        activo = parse_bool_param(self.request, "activo")
        if activo is not None:
            qs = qs.filter(activo=activo)

        stock_bajo = parse_bool_param(self.request, "stock_bajo")
        if stock_bajo is True:
            qs = qs.filter(cantidad_disponible__lte=F("stock_minimo"))
        elif stock_bajo is False:
            qs = qs.filter(cantidad_disponible__gt=F("stock_minimo"))

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(producto__nombre_producto__icontains=search)
                | Q(producto__codigo_de_barras__icontains=search)
            )

        return qs


@extend_schema_view(
    get=extend_schema(
        tags=["Inventario"],
        summary="Consultar detalle de un registro de inventario",
    ),
    patch=extend_schema(
        tags=["Inventario"],
        summary="Actualizar parcialmente un registro de inventario",
    ),
    put=extend_schema(
        tags=["Inventario"],
        summary="Actualizar un registro de inventario",
    ),
)
class ManagedInventoryDetailView(
    ManagedInventoryQueryset, generics.RetrieveUpdateAPIView
):
    http_method_names = ["get", "patch", "put", "head", "options"]


class ManagedInventoryDisableView(
    ManagedInventoryQueryset, generics.GenericAPIView
):
    serializer_class = InventoryDisableSerializer
    http_method_names = ["patch", "post", "head", "options"]

    def _disable(self, request, *args, **kwargs):
        inventario = self.get_object()

        if not inventario.activo:
            return Response(
                {"detail": "El registro de inventario ya se encuentra deshabilitado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventario.activo = False
        inventario.save(update_fields=["activo"])

        return Response(
            {
                "message": "Registro de inventario deshabilitado correctamente.",
                "id_inventario": inventario.id_inventario,
                "activo": inventario.activo,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Inventario"],
        summary="Deshabilitar registro de inventario (PATCH)",
        request=None,
        responses={
            200: InventoryDisableSerializer,
            400: OpenApiResponse(description="El inventario ya está deshabilitado."),
            403: OpenApiResponse(description="Sin permisos o sin sede asignada."),
            404: OpenApiResponse(description="Registro de inventario no encontrado."),
        },
    )
    def patch(self, request, *args, **kwargs):
        return self._disable(request, *args, **kwargs)

    @extend_schema(
        tags=["Inventario"],
        summary="Deshabilitar registro de inventario (POST)",
        request=None,
        responses={
            200: InventoryDisableSerializer,
            400: OpenApiResponse(description="El inventario ya está deshabilitado."),
            403: OpenApiResponse(description="Sin permisos o sin sede asignada."),
            404: OpenApiResponse(description="Registro de inventario no encontrado."),
        },
    )
    def post(self, request, *args, **kwargs):
        return self._disable(request, *args, **kwargs)