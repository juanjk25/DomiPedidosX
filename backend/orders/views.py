from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cliente, Pedido, Producto, Sede
from .serializers import (
    ClienteSerializer,
    CustomerAddressSerializer,
    DetallePedidoSerializer,
    PedidoSerializer,
    ProductoSerializer,
    RegisterSerializer,
    SedeSerializer,
)

User = get_user_model()


def current_cliente(user):
    return get_object_or_404(Cliente, credencial__usuario=user)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return current_cliente(self.request.user)

    def get_serializer_class(self):
        return ClienteSerializer


class BranchListView(generics.ListAPIView):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    permission_classes = [permissions.AllowAny]


class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, _request):
        categories = (
            Producto.objects.filter(activo=True)
            .values("tipo_de_producto")
            .distinct()
            .order_by("tipo_de_producto")
        )
        return Response(
            [
                {"id": index + 1, "name": item["tipo_de_producto"]}
                for index, item in enumerate(categories)
            ]
        )


class ProductListView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Producto.objects.filter(activo=True)
        sede_id = self.request.query_params.get("branch")
        if sede_id:
            queryset = queryset.filter(
                inventario__sede_id=sede_id,
                inventario__cantidad_disponible__gt=0,
            )
        category = self.request.query_params.get("category")
        if category and category != "all":
            queryset = queryset.filter(tipo_de_producto__iexact=category)
        return queryset.distinct()


class CustomerAddressListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cliente = current_cliente(request.user)
        if not cliente.direccion_residencia:
            return Response([])
        return Response(
            [
                {
                    "id": cliente.id_cliente,
                    "label": "Casa",
                    "address": cliente.direccion_residencia,
                    "reference": "",
                    "is_default": True,
                }
            ]
        )

    def post(self, request):
        serializer = CustomerAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cliente = current_cliente(request.user)
        cliente.direccion_residencia = serializer.validated_data["address"]
        cliente.save(update_fields=["direccion_residencia"])
        return Response(
            {
                "id": cliente.id_cliente,
                "label": serializer.validated_data.get("label", "Casa"),
                "address": cliente.direccion_residencia,
                "reference": serializer.validated_data.get("reference", ""),
                "is_default": True,
            },
            status=status.HTTP_201_CREATED,
        )


class CustomerAddressDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, _pk):
        cliente = current_cliente(request.user)
        cliente.direccion_residencia = ""
        cliente.save(update_fields=["direccion_residencia"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerListView(generics.ListAPIView):
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Cliente.objects.all().order_by("nombres", "apellidos")


class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic

    def get(self, request):
        pedidos = Pedido.objects.filter(cliente=current_cliente(request.user))
        return Response(PedidoSerializer(pedidos, many=True).data)

    @transaction.atomic
    def post(self, request):
        cliente = current_cliente(request.user)
        sede = get_object_or_404(Sede, pk=request.data.get("branch"))
        address = request.data.get("delivery_address", "").strip()
        items = request.data.get("items", [])
        if not address or not items:
            return Response(
                {"detail": "La dirección y los productos son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        prepared_items = []
        for item in items:
            producto = get_object_or_404(Producto, pk=item.get("product_id"))
            quantity = item.get("quantity")
            if not isinstance(quantity, int) or quantity <= 0:
                return Response(
                    {"detail": "La cantidad de cada producto debe ser positiva."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            inventory = (
                producto.inventarios.filter(sede=sede).select_for_update().first()
            )
            if not inventory or inventory.cantidad_disponible < quantity:
                return Response(
                    {"detail": f"No hay existencias para {producto.nombre_producto}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            prepared_items.append((producto, inventory, quantity))

        with transaction.atomic():
            pedido = Pedido.objects.create(
                cliente=cliente,
                sede=sede,
                direccion_entrega=address,
                notas_cliente=request.data.get("notes", ""),
            )
            for producto, inventory, quantity in prepared_items:
                DetallePedidoSerializer(
                    data={
                        "producto": producto.pk,
                        "cantidad": quantity,
                        "precio_unitario_aplicado": producto.precio_venta,
                    }
                ).is_valid(raise_exception=True)
                pedido.detalles.create(
                    producto=producto,
                    cantidad=quantity,
                    precio_unitario_aplicado=producto.precio_venta,
                )
                inventory.cantidad_disponible -= quantity
                inventory.save(update_fields=["cantidad_disponible"])
        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)


class OrderStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        status_map = {
            "received": "Pendiente",
            "preparing": "Preparando",
            "ready": "Preparando",
            "on_the_way": "En Camino",
            "delivered": "Entregado",
            "cancelled": "Cancelado",
        }
        pedido.estado_pedido = status_map.get(
            request.data.get("status"), request.data.get("status", pedido.estado_pedido)
        )
        pedido.save(update_fields=["estado_pedido"])
        return Response(PedidoSerializer(pedido).data)


class CustomerOrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        pedido = get_object_or_404(
            Pedido, pk=pk, cliente=current_cliente(request.user)
        )
        pedido.estado_pedido = "Cancelado"
        pedido.save(update_fields=["estado_pedido"])
        return Response(PedidoSerializer(pedido).data)
