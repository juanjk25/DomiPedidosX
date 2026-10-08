from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Branch, Category, CustomerAddress, Order, Product
from .permissions import IsOrderManager, IsStaffRole, role_of
from .serializers import BranchSerializer, CategorySerializer, CustomerAddressSerializer, CustomerListSerializer, OrderCreateSerializer, OrderSerializer, ProductSerializer, RegisterSerializer, UserSerializer
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user

class BranchListView(generics.ListAPIView):
    queryset = Branch.objects.filter(is_active=True)
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class CustomerAddressListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return CustomerAddress.objects.filter(customer=self.request.user)
    def perform_create(self, serializer):
        make_default = serializer.validated_data.get("is_default", False) or not self.get_queryset().exists()
        if make_default:
            self.get_queryset().update(is_default=False)
        serializer.save(customer=self.request.user, is_default=make_default)

class CustomerAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return CustomerAddress.objects.filter(customer=self.request.user)
    def perform_update(self, serializer):
        make_default = serializer.validated_data.get("is_default", self.get_object().is_default)
        if make_default:
            self.get_queryset().exclude(pk=self.get_object().pk).update(is_default=False)
        serializer.save(is_default=make_default)
    def perform_destroy(self, instance):
        customer = instance.customer
        was_default = instance.is_default
        instance.delete()
        if was_default:
            replacement = CustomerAddress.objects.filter(customer=customer).first()
            if replacement:
                replacement.is_default = True
                replacement.save(update_fields=["is_default"])

class CustomerListView(generics.ListAPIView):
    serializer_class = CustomerListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderManager]
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True, profile__role="customer").order_by("first_name", "last_name", "username")
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q
            queryset = queryset.filter(Q(username__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search))
        return queryset

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        queryset = Product.objects.select_related("branch", "category").filter(is_available=True, stock__gt=0, branch__is_active=True, category__is_active=True)
        for param, field in (("branch", "branch_id"), ("category", "category_id")):
            if self.request.query_params.get(param):
                queryset = queryset.filter(**{field: self.request.query_params[param]})
        if self.request.query_params.get("search"):
            queryset = queryset.filter(name__icontains=self.request.query_params["search"])
        return queryset

class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user, role = self.request.user, role_of(self.request.user)
        queryset = Order.objects.select_related("branch", "customer").prefetch_related("items")
        if role == "admin":
            branch_id = self.request.query_params.get("branch")
            return queryset.filter(branch_id=branch_id) if branch_id else queryset
        if role in {"operator", "kitchen", "courier"}:
            branch_id = getattr(getattr(user, "profile", None), "branch_id", None)
            return queryset.filter(branch_id=branch_id) if branch_id else queryset.none()
        return queryset.filter(customer=user)
    def get_serializer_class(self):
        return OrderCreateSerializer if self.request.method == "POST" else OrderSerializer
    def create(self, request, *args, **kwargs):
        role = role_of(request.user)
        if role not in {"customer", "operator", "admin"}:
            return Response({"detail": "Este rol no puede crear pedidos."}, status=status.HTTP_403_FORBIDDEN)
        if role == "customer" and "customer" in request.data:
            return Response({"detail": "No puedes crear pedidos a nombre de otro usuario."}, status=status.HTTP_403_FORBIDDEN)
        if role in {"operator", "admin"} and not request.data.get("customer"):
            return Response({"customer": "Selecciona el cliente para este pedido."}, status=status.HTTP_400_BAD_REQUEST)
        if role == "operator":
            branch_id = getattr(getattr(request.user, "profile", None), "branch_id", None)
            if not branch_id or str(branch_id) != str(request.data.get("branch")):
                return Response({"detail": "Solo puedes registrar pedidos para tu sede asignada."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffRole]
    transitions = {"received": {"preparing", "cancelled"}, "preparing": {"ready", "cancelled"}, "ready": {"on_the_way", "delivered"}, "on_the_way": {"delivered"}, "delivered": set(), "cancelled": set()}
    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        role = role_of(request.user)
        branch_id = getattr(getattr(request.user, "profile", None), "branch_id", None)
        if role != "admin" and not request.user.is_superuser and branch_id != order.branch_id:
            return Response({"detail": "No tienes acceso a esta sede."}, status=status.HTTP_403_FORBIDDEN)
        new_status = request.data.get("status")
        if new_status not in self.transitions.get(order.status, set()):
            return Response({"detail": "Cambio de estado no permitido."}, status=status.HTTP_400_BAD_REQUEST)
        allowed = {"operator": {"preparing", "ready", "on_the_way", "delivered", "cancelled"}, "kitchen": {"preparing", "ready", "cancelled"}, "courier": {"on_the_way", "delivered"}, "admin": set(self.transitions)}
        if new_status not in allowed.get(role, set()):
            return Response({"detail": "Tu rol no puede asignar ese estado."}, status=status.HTTP_403_FORBIDDEN)
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        return Response(OrderSerializer(order).data)

class CustomerOrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(Order.objects.select_for_update().prefetch_related("items__product"), pk=pk)
        if order.customer_id != request.user.id:
            return Response({"detail": "No tienes permiso para cancelar este pedido."}, status=status.HTTP_403_FORBIDDEN)
        if order.status != Order.Status.RECEIVED:
            return Response({"detail": "Solo puedes cancelar antes de que empiece la preparación."}, status=status.HTTP_400_BAD_REQUEST)
        for item in order.items.all():
            product = Product.objects.select_for_update().get(pk=item.product_id)
            product.stock += item.quantity
            product.save(update_fields=["stock"])
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return Response(OrderSerializer(order).data)
