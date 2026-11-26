from django.dispatch import Signal

# Parámetros enviados al dispararse:
# sender=Pedido, pedido, estado_anterior, estado_nuevo, usuario, rol_usuario, timestamp, historial
pedido_estado_cambiado = Signal()