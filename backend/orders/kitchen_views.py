from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DetallePedido, Pedido
from .permissions import (
    IsKitchenStaffOrAdmin,
    branch_of,
    role_of,
)
from .serializers import (
    PedidoCocinaSerializer,
    PedidosCocinaRespuestaSerializer,
)


class KitchenOrderQueueView(APIView):
    permission_classes = [IsKitchenStaffOrAdmin]

    queue_columns = {
        "recibidos": "Pendiente",
        "en_preparacion": "Preparando",
        "listos": "Listo",
    }

    @extend_schema(
        tags=["Cocina"],
        summary="Consultar la cola de pedidos de cocina",
        description=(
            "Devuelve los pedidos agrupados por estado. Cocina ve los pedidos "
            "de su sede y administración puede consultar todas las sedes."
        ),
        responses={
            200: PedidosCocinaRespuestaSerializer,
            401: OpenApiResponse(description="Se requiere autenticación."),
            403: OpenApiResponse(
                description="El usuario no tiene permiso o no tiene sede asignada."
            ),
        },
    )
    def get(self, request):
        pedidos = Pedido.objects.filter(
            estado_pedido__in=self.queue_columns.values()
        )

        if role_of(request.user) != "admin":
            sede_id = branch_of(request.user)

            if sede_id is None:
                return Response(
                    {"detail": "El usuario de cocina no tiene una sede asignada."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            pedidos = pedidos.filter(sede_id=sede_id)

        pedidos = (
            pedidos.prefetch_related(
                Prefetch(
                    "detalles",
                    queryset=DetallePedido.objects.select_related("producto"),
                )
            )
            .order_by("fecha_hora_pedido", "id_pedido")
        )

        pedidos_por_estado = {
            columna: [] for columna in self.queue_columns
        }
        columna_por_estado = {
            estado: columna
            for columna, estado in self.queue_columns.items()
        }

        datos = PedidoCocinaSerializer(pedidos, many=True).data

        for pedido in datos:
            columna = columna_por_estado[pedido["estado_pedido"]]
            pedidos_por_estado[columna].append(pedido)

        return Response({"pedidos_por_estado": pedidos_por_estado})