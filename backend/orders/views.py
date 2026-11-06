from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Cliente, Sede, Producto, Pedido
from .serializers import (
    RegisterSerializer,
    SedeSerializer,
    CategoriaSerializer,
    ProductoSerializer,
    PedidoSerializer,
    PedidoCreateSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Cuenta creada exitosamente.", "username": user.username},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        categorias = (
            Producto.objects
            .values_list("tipo_de_producto", flat=True)
            .distinct()
        )
        data = [
            {"id": index + 1, "nombre": nombre}
            for index, nombre in enumerate(categorias)
        ]
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
        serializer = PedidoCreateSerializer(data=request.data, context={"request": request})
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
            return Response({"error": "Pedido no encontrado."}, status=status.HTTP_404_NOT_FOUND)

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
            return Response({"error": "Pedido no encontrado."}, status=status.HTTP_404_NOT_FOUND)
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


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer