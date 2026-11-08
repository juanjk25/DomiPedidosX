from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

# Importamos los modelos actuales
from .models import Sede, Producto, Pedido, Cliente

# Importamos los nuevos serializadores
from .serializers import (
    SedeSerializer, 
    ProductoSerializer, 
    ClienteSerializer, 
    PedidoSerializer, 
    PedidoCreateSerializer, 
    RegisterSerializer, 
    UserSerializer,
    CustomTokenObtainPairSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class SedeListView(generics.ListAPIView):
    queryset = Sede.objects.all() # Asumimos que todas las creadas están activas
    serializer_class = SedeSerializer
    permission_classes = [permissions.AllowAny]

class ProductoListView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Producto.objects.filter(activo=True)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(nombre_producto__icontains=search)
        return queryset

class ClienteListView(generics.ListAPIView):
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Por ahora lo limitamos a superusuarios o puedes ajustarlo a empleados
        if not self.request.user.is_superuser:
            return Cliente.objects.none()
            
        queryset = Cliente.objects.all().order_by("nombres", "apellidos")
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(nombres__icontains=search) | 
                Q(apellidos__icontains=search) | 
                Q(correo_cliente__icontains=search)
            )
        return queryset

class PedidoListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Pedido.objects.select_related("sede", "cliente").prefetch_related("detalles")
        
        # Si es Admin, puede ver todo o filtrar por sede
        if user.is_superuser:
            sede_id = self.request.query_params.get("sede")
            return queryset.filter(sede_id=sede_id) if sede_id else queryset
            
        # Si es Cliente, ve solo sus pedidos
        if hasattr(user, 'cliente_credencial'):
            return queryset.filter(cliente=user.cliente_credencial.cliente)
            
        # Para otros empleados (Cajero, Repartidor), puedes expandir aquí la lógica
        return queryset.none()

    def get_serializer_class(self):
        return PedidoCreateSerializer if self.request.method == "POST" else PedidoSerializer

    def create(self, request, *args, **kwargs):
        # La validación central está en el CreateSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)

class PedidoStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    # Adaptado a estados en español
    transitions = {
        "Pendiente": {"En Preparación", "Cancelado"}, 
        "En Preparación": {"Listo", "Cancelado"}, 
        "Listo": {"En Camino", "Entregado"}, 
        "En Camino": {"Entregado"}, 
        "Entregado": set(), 
        "Cancelado": set()
    }

    def patch(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        
        # Validación de seguridad básica para el cambio de estado
        if not request.user.is_superuser:
            # Aquí puedes añadir la validación de si es empleado de la sede
            return Response({"detail": "No tienes acceso para cambiar este estado."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get("estado_pedido")
        
        # Como los estados ahora son texto libre en models.py con default "Pendiente", controlamos las transiciones:
        if new_status not in self.transitions.get(pedido.estado_pedido, set()):
            return Response({"detail": "Cambio de estado no permitido."}, status=status.HTTP_400_BAD_REQUEST)

        pedido.estado_pedido = new_status
        pedido.save(update_fields=["estado_pedido"])
        return Response(PedidoSerializer(pedido).data)

class ClientePedidoCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        
        if hasattr(request.user, 'cliente_credencial'):
            if pedido.cliente != request.user.cliente_credencial.cliente:
                return Response({"detail": "No tienes permiso para cancelar este pedido."}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "Acción no permitida."}, status=status.HTTP_403_FORBIDDEN)

        if pedido.estado_pedido != "Pendiente":
            return Response({"detail": "Solo puedes cancelar antes de que empiece la preparación."}, status=status.HTTP_400_BAD_REQUEST)

        # Se eliminó la reposición de stock directa al cancelar porque el modelo Producto no tiene campo stock.
        
        pedido.estado_pedido = "Cancelado"
        pedido.save(update_fields=["estado_pedido"])
        return Response(PedidoSerializer(pedido).data)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer