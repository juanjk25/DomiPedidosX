from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from .models import Branch, Category, CustomerAddress, Order, OrderItem, Product, UserProfile
User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True, default="")
    class Meta:
        model = UserProfile
        fields = ["role", "phone", "branch", "branch_name"]
    def get_role(self, obj):
        return "admin" if obj.user.is_superuser else obj.role

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    phone = serializers.CharField(source="profile.phone", required=False, allow_blank=True, write_only=True)
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_superuser", "profile", "phone"]
        read_only_fields = ["id", "username", "is_superuser"]
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if "phone" in profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            profile.phone = profile_data["phone"]
            profile.save(update_fields=["phone"])
        return instance

class CustomerListSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="profile.phone", read_only=True, default="")
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "phone"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "phone"]
        read_only_fields = ["id"]
    def validate_password(self, value):
        validate_password(value)
        return value
    def create(self, validated_data):
        phone = validated_data.pop("phone", "")
        user = User.objects.create_user(**validated_data)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.save(update_fields=["phone"])
        return user

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "address", "phone", "delivery_fee"]

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ["id", "label", "address", "reference", "is_default"]
        read_only_fields = ["id"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    can_order = serializers.BooleanField(read_only=True)
    class Meta:
        model = Product
        fields = ["id", "branch", "category", "category_name", "name", "description", "price", "preparation_minutes", "stock", "is_available", "can_order"]

class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "unit_price", "quantity", "line_total"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    payment_label = serializers.CharField(source="get_payment_method_display", read_only=True)
    class Meta:
        model = Order
        fields = ["id", "customer", "customer_name", "branch", "branch_name", "delivery_address", "notes", "payment_method", "payment_label", "status", "status_label", "subtotal", "delivery_fee", "total", "items", "created_at", "updated_at"]
        read_only_fields = fields

class OrderCreateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True, profile__role="customer"), required=False)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.filter(is_active=True))
    delivery_address = serializers.CharField(max_length=300)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    items = serializers.ListField(child=serializers.DictField(), min_length=1)
    def validate_items(self, items):
        normalized = []
        for item in items:
            try:
                product_id, quantity = int(item.get("product_id")), int(item.get("quantity"))
            except (TypeError, ValueError):
                raise serializers.ValidationError("Cada producto requiere product_id y quantity válidos.")
            if quantity < 1 or quantity > 20:
                raise serializers.ValidationError("La cantidad por producto debe estar entre 1 y 20.")
            normalized.append({"product_id": product_id, "quantity": quantity})
        return normalized
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        branch = validated_data["branch"]
        customer = validated_data.pop("customer", self.context["request"].user)
        products = {}
        for item in items_data:
            product = Product.objects.select_for_update().select_related("category", "branch").filter(pk=item["product_id"], branch=branch).first()
            if not product or not product.can_order:
                raise serializers.ValidationError({"items": f"El producto {item['product_id']} no está disponible en esta sede."})
            products[product.pk] = (product, products.get(product.pk, (None, 0))[1] + item["quantity"])
        for product, quantity in products.values():
            if quantity > product.stock:
                raise serializers.ValidationError({"items": f"No hay existencias suficientes de {product.name}."})
        subtotal = sum(product.price * quantity for product, quantity in products.values())
        fee = branch.delivery_fee
        order = Order.objects.create(customer=customer, subtotal=subtotal, delivery_fee=fee, total=subtotal + fee, **validated_data)
        for product, quantity in products.values():
            OrderItem.objects.create(order=order, product=product, product_name=product.name, unit_price=product.price, quantity=quantity)
            product.stock -= quantity
            product.save(update_fields=["stock"])
        return order
