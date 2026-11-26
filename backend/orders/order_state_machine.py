from django.db import transaction
from django.utils import timezone

from .models import HistorialEstadoPedido, Pedido
from .permissions import branch_of, role_of
from .signals import pedido_estado_cambiado

# Matriz formal: estado_actual -> {estado_siguiente: rol_autorizado}
ALLOWED_TRANSITIONS = {
    Pedido.Estado.PENDIENTE: {
        Pedido.Estado.PREPARANDO: "kitchen",
    },
    Pedido.Estado.PREPARANDO: {
        Pedido.Estado.LISTO: "kitchen",
    },
    Pedido.Estado.LISTO: {
        Pedido.Estado.EN_CAMINO: "courier",
    },
    Pedido.Estado.EN_CAMINO: {
        Pedido.Estado.ENTREGADO: "courier",
    },
}

ROLE_LABELS = {
    "kitchen": "cocinero",
    "courier": "repartidor",
}


class OrderStateError(Exception):
    """Error base para fallos en la transición de estado de un pedido."""


class OrderStatePermissionError(OrderStateError):
    """El usuario no tiene permiso por rol o por sede (HTTP 403)."""


class OrderStateTransitionError(OrderStateError):
    """La transición solicitada no es válida según la máquina de estados (HTTP 400)."""


def allowed_next_states(estado_actual):
    """Devuelve la lista de estados siguientes permitidos desde el estado actual."""
    return list(ALLOWED_TRANSITIONS.get(estado_actual, {}).keys())


def transition_order_status(pedido_id, nuevo_estado, usuario):
    """
    Valida y ejecuta la transición de estado de un pedido de forma atómica.

    Retorna una tupla (pedido, historial) si la transición es exitosa.
    Lanza:
        - Pedido.DoesNotExist si el pedido no existe.
        - OrderStatePermissionError si el rol o la sede no están autorizados.
        - OrderStateTransitionError si el estado o la transición no son válidos.
    """
    rol = role_of(usuario)
    if rol not in {"kitchen", "courier"}:
        raise OrderStatePermissionError(
            "Solo el personal de cocina o repartidores pueden actualizar el estado del pedido."
        )

    sede_usuario = branch_of(usuario)
    if sede_usuario is None:
        raise OrderStatePermissionError(
            "El usuario no tiene una sede asignada."
        )

    if nuevo_estado not in Pedido.Estado.values:
        raise OrderStateTransitionError(
            f"El estado '{nuevo_estado}' no es un estado válido."
        )

    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido_id)

        if pedido.sede_id != sede_usuario:
            raise OrderStatePermissionError(
                "No tienes permiso para actualizar pedidos de otra sede."
            )

        estado_anterior = pedido.estado_pedido
        transiciones_validas = ALLOWED_TRANSITIONS.get(estado_anterior, {})

        if nuevo_estado not in transiciones_validas:
            siguientes = allowed_next_states(estado_anterior)
            if siguientes:
                detalle = (
                    f"No se puede pasar de '{estado_anterior}' a '{nuevo_estado}'. "
                    f"Transiciones permitidas: {', '.join(siguientes)}."
                )
            else:
                detalle = (
                    f"El pedido en estado '{estado_anterior}' no admite más transiciones."
                )
            raise OrderStateTransitionError(detalle)

        rol_requerido = transiciones_validas[nuevo_estado]
        if rol != rol_requerido:
            raise OrderStatePermissionError(
                f"Solo un {ROLE_LABELS[rol_requerido]} puede cambiar el pedido "
                f"de '{estado_anterior}' a '{nuevo_estado}'."
            )

        timestamp = timezone.now()
        pedido.estado_pedido = nuevo_estado
        pedido.save(update_fields=["estado_pedido"])

        historial = HistorialEstadoPedido.objects.create(
            pedido=pedido,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            usuario=usuario,
            rol_usuario=rol,
            fecha_hora=timestamp,
        )

        transaction.on_commit(
            lambda: pedido_estado_cambiado.send(
                sender=Pedido,
                pedido=pedido,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                usuario=usuario,
                rol_usuario=rol,
                timestamp=timestamp,
                historial=historial,
            )
        )

    return pedido, historial