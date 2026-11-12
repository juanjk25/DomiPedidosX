from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Cliente, CredencialCliente, Sede, Producto, Pedido, DetallePedido

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    # Datos del usuario Django
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)

    # Datos del cliente
    nombres = serializers.CharField(max_length=50)
    apellidos = serializers.CharField(max_length=50)
    tipo_documento = serializers.ChoiceField(
        choices=[("CC", "CC"), ("CE", "CE"), ("NIT", "NIT"), ("TI", "TI")]
    )
    numero_documento = serializers.CharField(max_length=20)
    telefono_cliente = serializers.CharField(
        max_length=15, required=False, allow_blank=True
    )
    extension_telefonica = serializers.CharField(
        max_length=10, required=False, allow_blank=True
    )
    direccion_residencia = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )
    referencia_direccion = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )
    latitud = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-90,
        max_value=90,
        required=False,
        allow_null=True,
    )
    longitud = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-180,
        max_value=180,
        required=False,
        allow_null=True,
    )
    fecha_nacimiento = serializers.DateField()

    def validate_email(self, value):
        value = value.strip().lower()

        correo_en_uso = (
            User.objects.filter(username__iexact=value).exists()
            or User.objects.filter(email__iexact=value).exists()
            or Cliente.objects.filter(correo_cliente__iexact=value).exists()
        )

        if correo_en_uso:
            raise serializers.ValidationError(
                "Ya existe una cuenta con este correo."
            )

        return value

    def validate(self, attrs):
        tiene_latitud = attrs.get("latitud") is not None
        tiene_longitud = attrs.get("longitud") is not None

        if tiene_latitud != tiene_longitud:
            raise serializers.ValidationError(
                {"latitud": "Envía latitud y longitud juntas."}
            )

        return attrs

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=validated_data["nombres"],
            last_name=validated_data["apellidos"],
        )

        cliente = Cliente.objects.create(
            nombres=validated_data["nombres"],
            apellidos=validated_data["apellidos"],
            tipo_documento=validated_data["tipo_documento"],
            numero_documento=validated_data["numero_documento"],
            telefono_cliente=validated_data.get("telefono_cliente", ""),
            extension_telefonica=validated_data.get("extension_telefonica", ""),
            correo_cliente=email,
            direccion_residencia=validated_data.get("direccion_residencia", ""),
            referencia_direccion=validated_data.get("referencia_direccion", ""),
            latitud=validated_data.get("latitud"),
            longitud=validated_data.get("longitud"),
            fecha_nacimiento=validated_data["fecha_nacimiento"],
        )

        CredencialCliente.objects.create(
            cliente=cliente,
            usuario=user,
        )

        return user


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = [
            "id_sede",
            "nombre_sede",
            "barrio_sede",
            "direccion",
            "horario_atencion_apertura",
            "horario_atencion_cierre",
        ]


class SedeHorarioSerializer(serializers.ModelSerializer):
    """Serializer para consultar y actualizar el horario de atención de una sede (HU-E8)."""

    esta_abierta = serializers.SerializerMethodField()

    class Meta:
        model = Sede
        fields = [
            "id_sede",
            "nombre_sede",
            "horario_atencion_apertura",
            "horario_atencion_cierre",
            "esta_abierta",
        ]
        read_only_fields = ["id_sede", "nombre_sede", "esta_abierta"]

    def get_esta_abierta(self, obj):
        return obj.esta_en_horario()

    def validate(self, data):
        """Valida que la hora de cierre sea posterior a la de apertura."""
        apertura = data.get(
            "horario_atencion_apertura",
            getattr(self.instance, "horario_atencion_apertura", None),
        )
        cierre = data.get(
            "horario_atencion_cierre",
            getattr(self.instance, "horario_atencion_cierre", None),
        )

        if apertura and cierre and apertura >= cierre:
            raise serializers.ValidationError({
                "horario_atencion_cierre": (
                    "La hora de cierre debe ser posterior a la hora de apertura."
                )
            })
        return data


class CategoriaSerializer(serializers.Serializer):
    """Categorías derivadas del campo tipo_de_producto de Producto."""

    id = serializers.IntegerField()
    nombre = serializers.CharField()


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = [
            "id_producto",
            "codigo_de_barras",
            "nombre_producto",
            "tipo_de_producto",
            "activo",
            "precio_venta",
        ]


class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = [
            "id_linea",
            "producto",
            "cantidad",
            "precio_unitario_aplicado",
            "subtotal_linea",
            "iva_aplicado",
        ]


class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id_pedido",
            "cliente",
            "sede",
            "estado_pedido",
            "direccion_entrega",
            "notas_cliente",
            "fecha_hora_pedido",
            "tiempo_estimado_entrega",
            "detalles",
        ]
        read_only_fields = fields


class PedidoCreateSerializer(serializers.Serializer):
    sede = serializers.PrimaryKeyRelatedField(queryset=Sede.objects.all())
    direccion_entrega = serializers.CharField(max_length=150)
    notas_cliente = serializers.CharField(
        max_length=500, required=False, allow_blank=True
    )
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )

    def validate_items(self, items):
        normalized = []

        for item in items:
            try:
                producto_id = int(item.get("producto_id"))
                cantidad = int(item.get("cantidad"))
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    "Cada item requiere producto_id y cantidad válidos."
                )

            if cantidad < 1 or cantidad > 20:
                raise serializers.ValidationError(
                    "La cantidad debe estar entre 1 y 20."
                )

            normalized.append(
                {
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                }
            )

        return normalized

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        request = self.context["request"]
        cliente = Cliente.objects.get(credencial__usuario=request.user)

        pedido = Pedido.objects.create(
            cliente=cliente,
            sede=validated_data["sede"],
            direccion_entrega=validated_data["direccion_entrega"],
            notas_cliente=validated_data.get("notas_cliente", ""),
        )

        for item in items_data:
            producto = Producto.objects.get(pk=item["producto_id"])
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=item["cantidad"],
                precio_unitario_aplicado=producto.precio_venta,
            )

        return pedido


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

class TeamMemberStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = "admin" if user.is_superuser else "cliente"
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": "admin" if self.user.is_superuser else "cliente",
        }
        return data