from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Cliente, CredencialCliente, DetallePedido, Pedido, Producto, Sede

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(source="correo_cliente")
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(source="nombres", max_length=50)
    last_name = serializers.CharField(source="apellidos", max_length=50)
    phone = serializers.CharField(
        source="telefono_cliente", required=False, allow_blank=True
    )
    tipo_documento = serializers.ChoiceField(
        choices=("CC", "CE", "NIT", "TI"), required=False, default="CC"
    )
    numero_documento = serializers.CharField(required=False, default="")
    date_of_birth = serializers.DateField(source="fecha_nacimiento")

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        correo = validated_data["correo_cliente"]
        numero = validated_data.get("numero_documento") or correo.split("@")[0][:20]
        cliente = Cliente.objects.create(
            numero_documento=numero,
            fecha_nacimiento=validated_data.pop("fecha_nacimiento", None),
            **validated_data,
        )
        user = User.objects.create_user(
            username=correo,
            email=correo,
            password=password,
            first_name=cliente.nombres,
            last_name=cliente.apellidos,
        )
        CredencialCliente.objects.create(cliente=cliente, usuario=user)
        return cliente

    def to_representation(self, instance):
        return {
            "id": instance.id_cliente,
            "username": instance.correo_cliente,
            "email": instance.correo_cliente,
            "first_name": instance.nombres,
            "last_name": instance.apellidos,
        }


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id_cliente",
            "tipo_documento",
            "numero_documento",
            "nombres",
            "apellidos",
            "telefono_cliente",
            "correo_cliente",
            "direccion_residencia",
            "fecha_nacimiento",
        ]


class SedeSerializer(serializers.ModelSerializer):
    delivery_fee = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, default=0
    )

    class Meta:
        model = Sede
        fields = [
            "id_sede",
            "nombre_sede",
            "barrio_sede",
            "ciudad",
            "direccion",
            "horario_atencion_apertura",
            "horario_atencion_cierre",
            "delivery_fee",
        ]


class ProductoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="id_producto", read_only=True)
    name = serializers.CharField(source="nombre_producto", read_only=True)
    price = serializers.DecimalField(
        source="precio_venta", max_digits=12, decimal_places=2, read_only=True
    )
    branch = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="tipo_de_producto", read_only=True)
    description = serializers.SerializerMethodField()
    preparation_minutes = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            "id",
            "id_producto",
            "codigo_de_barras",
            "nombre_producto",
            "tipo_de_producto",
            "activo",
            "precio_compra",
            "precio_venta",
            "name",
            "price",
            "stock",
            "branch",
            "category",
            "category_name",
            "description",
            "preparation_minutes",
        ]

    def get_branch(self, obj):
        inventory = obj.inventarios.first()
        return inventory.sede_id if inventory else None

    def get_category(self, obj):
        return obj.tipo_de_producto

    def get_description(self, obj):
        return f"{obj.nombre_producto} preparado con ingredientes frescos."

    def get_preparation_minutes(self, obj):
        return 20

    def get_stock(self, obj):
        branch_id = self.context["request"].query_params.get("branch")
        inventories = obj.inventarios.all()
        if branch_id:
            inventories = inventories.filter(sede_id=branch_id)
        return sum(item.cantidad_disponible for item in inventories)


class DetallePedidoSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="producto.nombre_producto", read_only=True)

    class Meta:
        model = DetallePedido
        fields = [
            "id_linea",
            "producto",
            "product_name",
            "cantidad",
            "precio_unitario_aplicado",
            "subtotal_linea",
            "iva_aplicado",
        ]


class PedidoSerializer(serializers.ModelSerializer):
    items = DetallePedidoSerializer(source="detalles", many=True, read_only=True)
    customer_name = serializers.CharField(source="cliente.nombre_completo", read_only=True)
    branch_name = serializers.CharField(source="sede.nombre_sede", read_only=True)
    status = serializers.CharField(source="estado_pedido", read_only=True)
    id = serializers.IntegerField(source="id_pedido", read_only=True)
    branch = serializers.IntegerField(source="sede_id", read_only=True)
    status_label = serializers.CharField(source="estado_pedido", read_only=True)
    payment_label = serializers.CharField(read_only=True, default="Efectivo")
    subtotal = serializers.SerializerMethodField()
    delivery_fee = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, default=0
    )
    total = serializers.SerializerMethodField()
    delivery_address = serializers.CharField(source="direccion_entrega", read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id_pedido",
            "id",
            "branch",
            "customer_name",
            "branch_name",
            "delivery_address",
            "notas_cliente",
            "status",
            "status_label",
            "payment_label",
            "subtotal",
            "delivery_fee",
            "total",
            "items",
            "fecha_hora_pedido",
            "tiempo_estimado_entrega",
        ]

    def get_subtotal(self, obj):
        return sum(
            detail.precio_unitario_aplicado * detail.cantidad
            for detail in obj.detalles.all()
        )

    def get_total(self, obj):
        return self.get_subtotal(obj)


class CustomerAddressSerializer(serializers.Serializer):
    label = serializers.CharField(required=False, default="Casa")
    address = serializers.CharField(max_length=150)
    reference = serializers.CharField(required=False, allow_blank=True)
    is_default = serializers.BooleanField(required=False, default=False)
