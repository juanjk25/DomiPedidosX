from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Cliente"
        OPERATOR = "operator", "Operador de sede"
        KITCHEN = "kitchen", "Cocina"
        COURIER = "courier", "Repartidor"
        ADMIN = "admin", "Administrador"
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=30, blank=True)
    branch = models.ForeignKey("Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="staff")
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class Branch(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=240)
    phone = models.CharField(max_length=30, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ["name"]
    def __str__(self):
        return self.name

class CustomerAddress(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_addresses")
    label = models.CharField(max_length=60, default="Casa")
    address = models.CharField(max_length=300)
    reference = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    class Meta:
        ordering = ["-is_default", "label", "id"]
    def __str__(self):
        return f"{self.label}: {self.address}"

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"
    def __str__(self):
        return self.name

class Product(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    preparation_minutes = models.PositiveSmallIntegerField(default=20)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    class Meta:
        ordering = ["category__name", "name"]
    def __str__(self):
        return f"{self.name} - {self.branch.name}"
    @property
    def can_order(self):
        return self.is_available and self.stock > 0 and self.branch.is_active and self.category.is_active

class Order(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Recibido"
        PREPARING = "preparing", "En preparación"
        READY = "ready", "Listo para despacho"
        ON_THE_WAY = "on_the_way", "En camino"
        DELIVERED = "delivered", "Entregado"
        CANCELLED = "cancelled", "Cancelado"
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Efectivo"
        CARD = "card", "Tarjeta (simulada)"
        TRANSFER = "transfer", "Transferencia (simulada)"
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="orders")
    delivery_address = models.CharField(max_length=300)
    notes = models.CharField(max_length=500, blank=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return f"Pedido #{self.pk} - {self.get_status_display()}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=120)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveSmallIntegerField()
    @property
    def line_total(self):
        return self.unit_price * self.quantity
