from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Sede, Cliente, CredencialCliente, Producto, 
    Pedido, DetallePedido, Administrador, Cajero, Repartidor, OperadorSede
)

User = get_user_model()

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id_cliente", "tipo_documento", "numero_documento", "nombres", "apellidos", "telefono_cliente", "direccion_residencia"]

class UserSerializer(serializers.ModelSerializer):
    cliente = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_superuser", "cliente"]
        read_only_fields = ["id", "username", "is_superuser"]

    def get_cliente(self, obj):
        if hasattr(obj, 'cliente_credencial'):
            return ClienteSerializer(obj.cliente_credencial.cliente).data
        return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    numero_documento = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "telefono", "numero_documento"]
        read_only_fields = ["id"]

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        telefono = validated_data.pop("telefono", "")
        numero_documento = validated_data.pop("numero_documento", "")
        
        user = User.objects.create_user(**validated_data)
        
        # Crear el Cliente asociado
        cliente = Cliente.objects.create(
            tipo_documento="CC",
            numero_documento=numero_documento,
            nombres=user.first_name,
            apellidos=user.last_name,
            correo_cliente=user.email,
            telefono_cliente=telefono,
            fecha_nacimiento="2000-01-01" # Valor por defecto o ajustar según sea necesario
        )
        
        # Enlazar Usuario y Cliente
        CredencialCliente.objects.create(usuario=user, cliente=cliente)
        
        return user

class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ["id_sede", "nombre_sede", "barrio_sede", "direccion", "horario_atencion_apertura", "horario_atencion_cierre"]

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ["id_producto", "codigo_de_barras", "nombre_producto", "tipo_de_producto", "activo", "precio_venta"]

class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre_producto", read_only=True)
    
    class Meta:
        model = DetallePedido
        fields = ["id_linea", "producto", "producto_nombre", "cantidad", "precio_unitario_aplicado", "subtotal_linea"]

class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre_sede", read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            "id_pedido", "cliente", "cliente_nombre", "sede", "sede_nombre", 
            "repartidor", "estado_pedido", "direccion_entrega", "notas_cliente", 
            "fecha_hora_pedido", "tiempo_estimado_entrega", "detalles"
        ]
        read_only_fields = fields

class PedidoCreateSerializer(serializers.Serializer):
    cliente_id = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all(), required=False)
    sede_id = serializers.PrimaryKeyRelatedField(queryset=Sede.objects.all())
    direccion_entrega = serializers.CharField(max_length=150)
    notas_cliente = serializers.CharField(max_length=500, required=False, allow_blank=True)
    items = serializers.ListField(child=serializers.DictField(), min_length=1)

    def validate_items(self, items):
        normalized = []
        for item in items:
            try:
                producto_id, cantidad = int(item.get("producto_id")), int(item.get("cantidad"))
            except (TypeError, ValueError):
                raise serializers.ValidationError("Cada producto requiere producto_id y cantidad válidos.")
            if cantidad < 1 or cantidad > 20:
                raise serializers.ValidationError("La cantidad por producto debe estar entre 1 y 20.")
            normalized.append({"producto_id": producto_id, "cantidad": cantidad})
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        sede = validated_data["sede_id"]
        
        request_user = self.context["request"].user
        cliente = validated_data.pop("cliente_id", None)
        
        if not cliente:
            if hasattr(request_user, 'cliente_credencial'):
                cliente = request_user.cliente_credencial.cliente
            else:
                raise serializers.ValidationError("El usuario actual no tiene un perfil de cliente.")

        productos_a_procesar = {}
        for item in items_data:
            producto = Producto.objects.filter(pk=item["producto_id"], activo=True).first()
            if not producto:
                raise serializers.ValidationError({"items": f"El producto {item['producto_id']} no existe o no está activo."})
            productos_a_procesar[producto.pk] = (producto, item["cantidad"])

        pedido = Pedido.objects.create(
            cliente=cliente,
            sede=sede,
            direccion_entrega=validated_data["direccion_entrega"],
            notas_cliente=validated_data.get("notas_cliente", "")
        )

        for producto, cantidad in productos_a_procesar.values():
            subtotal = producto.precio_venta * cantidad
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario_aplicado=producto.precio_venta,
                subtotal_linea=subtotal
            )

        return pedido

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        
        role = "customer"
        if user.is_superuser:
            role = "admin"
        else:
            if Administrador.objects.filter(empleado__correo_empleado=user.email).exists():
                role = "administrador"
            elif Cajero.objects.filter(empleado__correo_empleado=user.email).exists():
                role = "cajero"
            elif Repartidor.objects.filter(empleado__correo_empleado=user.email).exists():
                role = "repartidor"
            elif OperadorSede.objects.filter(empleado__correo_empleado=user.email).exists():
                role = "operador"
                
        token['role'] = role
        return token
        
    def validate(self, attrs):
        data = super().validate(attrs)
        
        role = "customer"
        if self.user.is_superuser:
            role = "admin"
        else:
            if Administrador.objects.filter(empleado__correo_empleado=self.user.email).exists():
                role = "administrador"
            elif Cajero.objects.filter(empleado__correo_empleado=self.user.email).exists():
                role = "cajero"
            elif Repartidor.objects.filter(empleado__correo_empleado=self.user.email).exists():
                role = "repartidor"
            elif OperadorSede.objects.filter(empleado__correo_empleado=self.user.email).exists():
                role = "operador"

        data['user'] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": role
        }
        return data