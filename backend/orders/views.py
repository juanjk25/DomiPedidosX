import logging

from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (
    Cliente,
    Sede,
    Pedido,
    Producto,
    Categoria,
    AuditoriaPersonal,
    Inventario,
    Carrito,
    ItemCarrito,
)
from .permissions import role_of, branch_of, IsAdministrator, IsOrderManager
from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    TeamMemberStatusSerializer,
    TeamMemberSerializer,
    TeamMemberCreateSerializer,
    AuditoriaPersonalSerializer,
    SedeSerializer,
    SedeHorarioSerializer,
    PedidoSerializer,
    PedidoCreateSerializer,
    CustomerProfileUpdateSerializer,
    PasswordChangeSerializer,
    CustomTokenObtainPairSerializer,
    CarritoSerializer,
    CarritoAddItemSerializer,
    CarritoUpdateItemSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Cuenta creada exitosamente.",
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "nombres": user.first_name,
                    "apellidos": user.last_name,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip()

        # La misma respuesta evita revelar si el correo está registrado.
        users = User.objects.filter(email__iexact=email, is_active=True)

        for user in users:
            if not user.has_usable_password():
                continue

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = (
                f"{settings.FRONTEND_URL.rstrip('/')}/restablecer-contrasena"
                f"?uid={uid}&token={token}"
            )

            try:
                send_mail(
                    subject="Recupera tu contraseña de DomiPedidosX",
                    message=(
                        "Recibimos una solicitud para cambiar la contraseña de tu cuenta.\n\n"
                        f"Abre este enlace para elegir una nueva contraseña:\n{reset_url}\n\n"
                        "El enlace vence en una hora. Si no solicitaste el cambio, "
                        "ignora este correo."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception(
                    "No se pudo enviar un correo de recuperación de contraseña."
                )

        return Response(
            {
                "message": (
                    "Si existe una cuenta con ese correo, "
                    "enviaremos un enlace de recuperación."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            User.DoesNotExist,
        ):
            return Response(
                {"detail": "El enlace de recuperación no es válido o ya venció."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "El enlace de recuperación no es válido o ya venció."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = serializer.validated_data["new_password"]

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as error:
            return Response(
                {"new_password": error.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {"message": "La contraseña se actualizó correctamente."},
            status=status.HTTP_200_OK,
        )


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(
            {"message": "La contraseña se cambió correctamente."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": user.id, "email": user.email, "username": user.username,
            "role": role_of(user), "sede": branch_of(user),
            "can_manage_menu": role_of(user) in {"operator", "admin"},
        }
        try:
            cliente = Cliente.objects.get(credencial__usuario=user)
            data.update({
                "nombres": cliente.nombres, "apellidos": cliente.apellidos,
                "tipo_documento": cliente.tipo_documento,
                "numero_documento": cliente.numero_documento,
                "telefono": cliente.telefono_cliente,
                "telefono_cliente": cliente.telefono_cliente,
                "extension_telefonica": cliente.extension_telefonica,
                "direccion_residencia": cliente.direccion_residencia,
                "referencia_direccion": cliente.referencia_direccion,
                "latitud": str(cliente.latitud) if cliente.latitud is not None else None,
                "longitud": str(cliente.longitud) if cliente.longitud is not None else None,
                "fecha_nacimiento": cliente.fecha_nacimiento.isoformat(),
            })
        except Cliente.DoesNotExist:
            pass
        return Response(data)

    def patch(self, request):
        try:
            cliente = Cliente.objects.select_related("credencial__usuario").get(
                credencial__usuario=request.user
            )
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "Esta cuenta no tiene perfil de cliente."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerProfileUpdateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(cliente, serializer.validated_data)
        return MeView().get(request)


class BranchListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SedeSerializer
    queryset = Sede.objects.all()


class SedeHorarioView(generics.RetrieveUpdateAPIView):
    queryset = Sede.objects.all()
    serializer_class = SedeHorarioSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOrderManager()]


class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cliente = Cliente.objects.get(credencial__usuario=request.user)
        pedidos = Pedido.objects.filter(cliente=cliente).order_by("-fecha_hora_pedido")
        serializer = PedidoSerializer(pedidos, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PedidoCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            pedido = serializer.save()
            return Response(
                PedidoSerializer(pedido).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerOrderCancelView(APIView):
    """
    Cancela un pedido si aún no ha iniciado preparación en cocina (HU-C6, HU-C7).
    Roles permitidos: cliente (sus pedidos), operador (pedidos de su sede) y administrador.
    """

    permission_classes = [permissions.IsAuthenticated]
    NON_CANCELLABLE_STATES = {"Preparando", "Listo", "En Camino", "Entregado"}

    def post(self, request, pk):
        rol = role_of(request.user)
        if rol not in {"customer", "operator", "admin"}:
            return Response(
                {"error": "No tienes permiso para cancelar pedidos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            if rol == "customer":
                cliente = Cliente.objects.get(credencial__usuario=request.user)
                pedido = Pedido.objects.get(pk=pk, cliente=cliente)
            elif rol == "operator":
                sede_id = branch_of(request.user)
                pedido = Pedido.objects.get(pk=pk, sede_id=sede_id)
            else:
                pedido = Pedido.objects.get(pk=pk)
        except (Cliente.DoesNotExist, Pedido.DoesNotExist):
            return Response(
                {"error": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if pedido.estado_pedido == "Cancelado":
            return Response(
                {
                    "error": "El pedido ya fue cancelado previamente.",
                    "estado_pedido": pedido.estado_pedido,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pedido.estado_pedido in self.NON_CANCELLABLE_STATES or pedido.estado_pedido != "Pendiente":
            return Response(
                {
                    "error": (
                        "No se puede cancelar el pedido porque ya inició preparación "
                        "o se encuentra en una etapa posterior."
                    ),
                    "estado_pedido": pedido.estado_pedido,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            pedido.estado_pedido = "Cancelado"
            pedido.save(update_fields=["estado_pedido"])

            for detalle in pedido.detalles.select_related("producto"):
                inv = Inventario.objects.select_for_update().filter(
                    producto=detalle.producto,
                    sede=pedido.sede,
                ).first()
                if inv is not None:
                    inv.cantidad_disponible += detalle.cantidad
                    inv.save(update_fields=["cantidad_disponible"])

        return Response(
            {
                "message": "Pedido cancelado.",
                "id_pedido": pedido.id_pedido,
                "estado_pedido": pedido.estado_pedido,
            }
        )


def _get_or_create_cliente_cart(user):
    try:
        cliente = Cliente.objects.get(credencial__usuario=user)
    except Cliente.DoesNotExist:
        return None, None
    carrito, _ = Carrito.objects.get_or_create(cliente=cliente)
    return cliente, carrito


class CartView(APIView):
    """Consulta o vacía el carrito de compras del cliente autenticado (HU-C2)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cliente, carrito = _get_or_create_cliente_cart(request.user)
        if cliente is None:
            return Response(
                {"detail": "Esta cuenta no tiene perfil de cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )
        carrito = Carrito.objects.prefetch_related("items__producto").get(pk=carrito.pk)
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)

    def delete(self, request):
        cliente, carrito = _get_or_create_cliente_cart(request.user)
        if cliente is None:
            return Response(
                {"detail": "Esta cuenta no tiene perfil de cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )
        with transaction.atomic():
            carrito.items.all().delete()
            carrito.sede = None
            carrito.save(update_fields=["sede", "actualizado_en"])
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)


class CartItemAddView(APIView):
    """Agrega un producto al carrito o incrementa su cantidad si ya existe (HU-C2)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cliente, carrito = _get_or_create_cliente_cart(request.user)
        if cliente is None:
            return Response(
                {"detail": "Esta cuenta no tiene perfil de cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CarritoAddItemSerializer(
            data=request.data,
            context={"carrito": carrito},
        )
        serializer.is_valid(raise_exception=True)

        producto = serializer.validated_data["producto"]
        sede = serializer.validated_data["sede"]
        cantidad = serializer.validated_data["cantidad"]

        with transaction.atomic():
            if carrito.sede_id != sede.pk:
                carrito.sede = sede
                carrito.save(update_fields=["sede", "actualizado_en"])
            item, created = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                defaults={"cantidad": cantidad},
            )
            if not created:
                item.cantidad += cantidad
                item.save(update_fields=["cantidad"])

        carrito = Carrito.objects.prefetch_related("items__producto").get(pk=carrito.pk)
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)


class CartItemDetailView(APIView):
    """Actualiza la cantidad o elimina una línea del carrito (HU-C2)."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, producto_id):
        cliente, carrito = _get_or_create_cliente_cart(request.user)
        if cliente is None:
            return Response(
                {"detail": "Esta cuenta no tiene perfil de cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            item = ItemCarrito.objects.select_related("producto").get(
                carrito=carrito, producto_id=producto_id
            )
        except ItemCarrito.DoesNotExist:
            return Response(
                {"detail": "El producto no está en el carrito."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CarritoUpdateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nueva_cantidad = serializer.validated_data["cantidad"]

        with transaction.atomic():
            if nueva_cantidad == 0:
                item.delete()
                if not carrito.items.exists():
                    carrito.sede = None
                    carrito.save(update_fields=["sede", "actualizado_en"])
            else:
                inv = Inventario.objects.filter(
                    producto=item.producto, sede=carrito.sede
                ).first()
                if inv is not None and nueva_cantidad > inv.cantidad_disponible:
                    return Response(
                        {
                            "cantidad": [
                                f"Solo hay {inv.cantidad_disponible} unidades disponibles en esta sede."
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                item.cantidad = nueva_cantidad
                item.save(update_fields=["cantidad"])

        carrito = Carrito.objects.prefetch_related("items__producto").get(pk=carrito.pk)
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)

    def delete(self, request, producto_id):
        cliente, carrito = _get_or_create_cliente_cart(request.user)
        if cliente is None:
            return Response(
                {"detail": "Esta cuenta no tiene perfil de cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        deleted, _ = ItemCarrito.objects.filter(
            carrito=carrito, producto_id=producto_id
        ).delete()
        if not deleted:
            return Response(
                {"detail": "El producto no está en el carrito."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not carrito.items.exists():
            carrito.sede = None
            carrito.save(update_fields=["sede", "actualizado_en"])

        carrito = Carrito.objects.prefetch_related("items__producto").get(pk=carrito.pk)
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)


class OrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            cliente = Cliente.objects.get(credencial__usuario=request.user)
            pedido = Pedido.objects.get(pk=pk, cliente=cliente)
        except (Cliente.DoesNotExist, Pedido.DoesNotExist):
            return Response(
                {"error": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"estado": pedido.estado_pedido})


class CustomerListView(APIView):
    permission_classes = [IsOrderManager]

    def get(self, request):
        clientes = Cliente.objects.select_related("credencial__usuario").all()
        data = [
            {
                "id": c.id_cliente,
                "nombres": c.nombres,
                "apellidos": c.apellidos,
                "correo": c.correo_cliente,
                "telefono": c.telefono_cliente,
            }
            for c in clientes
        ]
        return Response(data)


class TeamMemberListCreateView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        workers = User.objects.filter(is_staff=True).select_related(
            "perfil_trabajador__sede"
        ).order_by("-date_joined")
        return Response(TeamMemberSerializer(workers, many=True).data)

    def post(self, request):
        serializer = TeamMemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            TeamMemberSerializer(serializer.save()).data,
            status=status.HTTP_201_CREATED,
        )


class TeamMemberStatusView(APIView):
    permission_classes = [IsAdministrator]

    def patch(self, request, pk):
        serializer = TeamMemberStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            member = User.objects.get(pk=pk, is_staff=True)
        except User.DoesNotExist:
            return Response(
                {"detail": "No se encontró la cuenta del integrante."},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_active = serializer.validated_data["is_active"]
        motivo = serializer.validated_data.get("motivo", "").strip()

        if member.pk == request.user.pk and not is_active:
            return Response(
                {
                    "detail": (
                        "No puedes desactivar la cuenta con la que tienes esta sesión."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        estado_anterior = member.is_active

        with transaction.atomic():
            member.is_active = is_active
            member.save(update_fields=["is_active"])

            auditoria = AuditoriaPersonal.objects.create(
                administrador=request.user,
                usuario_afectado=member,
                estado_anterior=estado_anterior,
                estado_nuevo=is_active,
                motivo=motivo,
            )

        logger.info(
            "Auditoría personal: admin=%s cambió is_active de %s (%s -> %s)",
            request.user.username,
            member.username,
            estado_anterior,
            is_active,
        )

        return Response(
            {
                "id": member.id,
                "username": member.username,
                "email": member.email,
                "is_active": member.is_active,
                "auditoria": AuditoriaPersonalSerializer(auditoria).data,
            }
        )


class TeamMemberAuditListView(generics.ListAPIView):
    permission_classes = [IsAdministrator]
    serializer_class = AuditoriaPersonalSerializer

    def get_queryset(self):
        return AuditoriaPersonal.objects.select_related(
            "administrador", "usuario_afectado"
        ).all()


class CustomTokenObtainPairView(TokenObtainPairView):
    authentication_classes = []
    serializer_class = CustomTokenObtainPairSerializer