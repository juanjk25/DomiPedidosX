from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Pedido
from .order_state_machine import (
    OrderStatePermissionError,
    OrderStateTransitionError,
    transition_order_status,
)
from .permissions import IsKitchenOrDeliveryStaff
from .serializers import (
    PedidoEstadoRespuestaSerializer,
    PedidoEstadoUpdateSerializer,
)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsKitchenOrDeliveryStaff]

    @extend_schema(
        tags=["Pedidos"],
        summary="Actualizar el estado de un pedido",
        description=(
            "Ejecuta una transición válida en la máquina de estados del pedido. "
            "Cocinero puede avanzar Pendiente -> Preparando -> Listo. "
            "Repartidor puede avanzar Listo -> En camino -> Entregado. "
            "Restringido a pedidos de la sede asignada al usuario."
        ),
        request=PedidoEstadoUpdateSerializer,
        responses={
            200: PedidoEstadoRespuestaSerializer,
            400: OpenApiResponse(
                description="Estado inválido o transición no permitida."
            ),
            401: OpenApiResponse(description="Se requiere autenticación."),
            403: OpenApiResponse(
                description=(
                    "El usuario no tiene permiso para esta transición, "
                    "no tiene sede asignada o el pedido pertenece a otra sede."
                )
            ),
            404: OpenApiResponse(description="Pedido no encontrado."),
        },
    )
    def patch(self, request, pk):
        serializer = PedidoEstadoUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nuevo_estado = serializer.validated_data["estado"]

        try:
            pedido, historial = transition_order_status(
                pedido_id=pk,
                nuevo_estado=nuevo_estado,
                usuario=request.user,
            )
        except Pedido.DoesNotExist:
            return Response(
                {"detail": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except OrderStatePermissionError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except OrderStateTransitionError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        historial_completo = list(
            pedido.historial_estados.select_related("usuario").order_by(
                "fecha_hora", "id"
            )
        )

        timestamps_por_etapa = {
            Pedido.Estado.PENDIENTE: pedido.fecha_hora_pedido,
        }
        for registro in historial_completo:
            timestamps_por_etapa[registro.estado_nuevo] = registro.fecha_hora

        respuesta = PedidoEstadoRespuestaSerializer(
            {
                "id_pedido": pedido.id_pedido,
                "sede_id": pedido.sede_id,
                "estado_anterior": historial.estado_anterior,
                "estado_actual": pedido.estado_pedido,
                "fecha_cambio": historial.fecha_hora,
                "timestamps_por_etapa": timestamps_por_etapa,
                "historial": historial_completo,
            }
        )
        return Response(respuesta.data, status=status.HTTP_200_OK)