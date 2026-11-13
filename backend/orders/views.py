import logging

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
from .models import Cliente, Sede, Producto, Pedido, Categoria
from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    TeamMemberStatusSerializer,
    TeamMemberSerializer,
    TeamMemberCreateSerializer,
    SedeSerializer,
    CategoriaSerializer,
    ProductoSerializer,
    PedidoSerializer,
    PedidoCreateSerializer,
    CustomTokenObtainPairSerializer,
)
from .permissions import IsStaffRole

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(APIView):
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


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            cliente = Cliente.objects.get(credencial__usuario=user)
            return Response({
                "id": user.id,
                "email": user.email,
                "nombres": cliente.nombres,
                "apellidos": cliente.apellidos,
                "telefono": cliente.telefono_cliente,
            })
        except Cliente.DoesNotExist:
            return Response({
                "id": user.id,
                "email": user.email,
                "role": "admin",
            })


class BranchListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SedeSerializer
    queryset = Sede.objects.all()


class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categorias = Categoria.objects.filter(activa=True)
        data = [{"id": c.id_categoria, "nombre": c.nombre} for c in categorias]
        return Response(data)


class ProductListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductoSerializer

    def get_queryset(self):
        qs = Producto.objects.filter(activo=True)
        categoria = self.request.query_params.get("categoria")
        if categoria:
            qs = qs.filter(tipo_de_producto=categoria)
        return qs


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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            cliente = Cliente.objects.get(credencial__usuario=request.user)
            pedido = Pedido.objects.get(pk=pk, cliente=cliente)
        except (Cliente.DoesNotExist, Pedido.DoesNotExist):
            return Response(
                {"error": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if pedido.estado_pedido != "Pendiente":
            return Response(
                {"error": "Solo se pueden cancelar pedidos en estado Pendiente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pedido.estado_pedido = "Cancelado"
        pedido.save(update_fields=["estado_pedido"])
        return Response({"message": "Pedido cancelado."})


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
    permission_classes = [permissions.IsAdminUser]

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
    """
    Vista administrativa para gestionar el equipo laboral (HU-A9).
    - GET: Lista los integrantes del equipo de trabajo (solo administradores).
    - POST: Registra un nuevo trabajador con rol asignado (solo administradores).
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        trabajadores = User.objects.filter(is_staff=True).order_by("-date_joined")
        serializer = TeamMemberSerializer(trabajadores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TeamMemberCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                TeamMemberSerializer(user).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamMemberStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

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

        if member.pk == request.user.pk and not is_active:
            return Response(
                {
                    "detail": (
                        "No puedes desactivar la cuenta con la que tienes esta sesión."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.is_active = is_active
        member.save(update_fields=["is_active"])

        return Response({
            "id": member.id,
            "username": member.username,
            "email": member.email,
            "is_active": member.is_active,
        })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class OperatorCategoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffRole]

    def get(self, request):
        categorias = Categoria.objects.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategoriaSerializer(data=request.data)
        if serializer.is_valid():
            categoria = serializer.save()
            return Response(CategoriaSerializer(categoria).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OperatorCategoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffRole]

    def patch(self, request, pk):
        try:
            categoria = Categoria.objects.get(pk=pk)
        except Categoria.DoesNotExist:
            return Response({"error": "Categoría no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        
        activa = request.data.get('activa')
        if activa is not None:
            categoria.activa = activa
            categoria.save(update_fields=['activa'])
            
        return Response(CategoriaSerializer(categoria).data)