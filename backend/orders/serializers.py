from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from datetime import date
import re
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    Cliente,
    CredencialCliente,
    Sede,
    Producto,
    Inventario,
    Pedido,
    DetallePedido,
    PerfilTrabajador,
    Categoria,
    CredencialEmpleado,
    AuditoriaPersonal,
    Carrito,
    ItemCarrito,
)
from .permissions import role_of, branch_of


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

    def validate_nombres(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los nombres solo pueden contener letras.")
        return value

    def validate_apellidos(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los apellidos solo pueden contener letras.")
        return value

    def validate_fecha_nacimiento(self, value):
        today = date.today()
        if value < date(1930, 1, 1):
            raise serializers.ValidationError("La fecha de nacimiento debe ser desde 1930.")
        if value > today:
            raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")
        return value


    def validate_nombres(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los nombres solo pueden contener letras.")
        return value

    def validate_apellidos(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los apellidos solo pueden contener letras.")
        return value

    def validate_fecha_nacimiento(self, value):
        today = date.today()
        if value < date(1930, 1, 1):
            raise serializers.ValidationError("La fecha de nacimiento debe ser desde 1930.")
        if value > today:
            raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")
        return value

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
        apertura = data.get(
            "horario_atencion_apertura",
            getattr(self.instance, "horario_atencion_apertura", None),
        )
        cierre = data.get(
            "horario_atencion_cierre",
            getattr(self.instance, "horario_atencion_cierre", None),
        )
        if apertura and cierre and apertura >= cierre:
            raise serializers.ValidationError(
                {"horario_atencion_cierre": "La hora de cierre debe ser posterior a la hora de apertura."}
            )
        return data


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


# Serializadores para la cola de pedidos de cocina
class PedidoCocinaItemSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(read_only=True)
    nombre_producto = serializers.CharField(
        source="producto.nombre_producto",
        read_only=True,
    )

    class Meta:
        model = DetallePedido
        fields = ["id_linea", "producto_id", "nombre_producto", "cantidad"]
        read_only_fields = fields


class PedidoCocinaSerializer(serializers.ModelSerializer):
    sede_id = serializers.IntegerField(read_only=True)
    detalles = PedidoCocinaItemSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id_pedido",
            "sede_id",
            "estado_pedido",
            "fecha_hora_pedido",
            "notas_cliente",
            "detalles",
        ]
        read_only_fields = fields


class PedidosCocinaColumnasSerializer(serializers.Serializer):
    recibidos = PedidoCocinaSerializer(many=True)
    en_preparacion = PedidoCocinaSerializer(many=True)
    listos = PedidoCocinaSerializer(many=True)


class PedidosCocinaRespuestaSerializer(serializers.Serializer):
    pedidos_por_estado = PedidosCocinaColumnasSerializer()


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
        try:
            cliente = Cliente.objects.get(credencial__usuario=request.user)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError({"detail": "Esta cuenta no tiene perfil de cliente."})
        from .catalog_views import in_branch, public_products
        product_ids = [item["producto_id"] for item in items_data]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError({"items": "Agrupa las cantidades de cada producto en una sola línea."})
        # Bloquea las filas mientras se confirma el pedido para validar la publicación.
        available = in_branch(public_products(), validated_data["sede"].pk).filter(pk__in=product_ids)
        available_ids = list(available.values_list("pk", flat=True))
        products = {p.pk: p for p in Producto.objects.select_for_update().filter(pk__in=available_ids)}
        if len(products) != len(product_ids) or any(not p.activo for p in products.values()):
            raise serializers.ValidationError({"items": "Un producto ya no está disponible en esta sede. Actualiza el menú."})

        # HU-B14: Validar y descontar inventario por sede de forma atómica.
        inventarios = {
            inv.producto_id: inv
            for inv in Inventario.objects.select_for_update().filter(
                sede=validated_data["sede"],
                producto_id__in=product_ids,
            )
        }
        for item in items_data:
            producto = products[item["producto_id"]]
            inv = inventarios.get(producto.pk)
            if inv is not None:
                if inv.cantidad_disponible <= 0:
                    raise serializers.ValidationError(
                        {"items": f"El producto '{producto.nombre_producto}' está agotado en esta sede."}
                    )
                if inv.cantidad_disponible < item["cantidad"]:
                    raise serializers.ValidationError(
                        {
                            "items": (
                                f"Stock insuficiente para '{producto.nombre_producto}' "
                                f"(disponibles: {inv.cantidad_disponible})."
                            )
                        }
                    )

        pedido = Pedido.objects.create(
            cliente=cliente,
            sede=validated_data["sede"],
            direccion_entrega=validated_data["direccion_entrega"],
            notas_cliente=validated_data.get("notas_cliente", ""),
        )

        for item in items_data:
            producto = products[item["producto_id"]]
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=item["cantidad"],
                precio_unitario_aplicado=producto.precio_venta,
            )
            inv = inventarios.get(producto.pk)
            if inv is not None:
                inv.cantidad_disponible -= item["cantidad"]
                inv.save(update_fields=["cantidad_disponible"])

        return pedido


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)


class TeamMemberStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
    motivo = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class AuditoriaPersonalSerializer(serializers.ModelSerializer):
    administrador_username = serializers.CharField(
        source="administrador.username", read_only=True
    )
    usuario_afectado_username = serializers.CharField(
        source="usuario_afectado.username", read_only=True
    )

    class Meta:
        model = AuditoriaPersonal
        fields = [
            "id",
            "administrador",
            "administrador_username",
            "usuario_afectado",
            "usuario_afectado_username",
            "estado_anterior",
            "estado_nuevo",
            "motivo",
            "fecha_hora",
        ]
        read_only_fields = fields


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "La contraseña actual no es correcta."}
            )
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas nuevas no coinciden."}
            )
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"new_password": error.messages})
        return attrs


class CustomerProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)
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

    def validate_nombres(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los nombres solo pueden contener letras.")
        return value

    def validate_apellidos(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los apellidos solo pueden contener letras.")
        return value

    def validate_fecha_nacimiento(self, value):
        today = date.today()
        if value < date(1930, 1, 1):
            raise serializers.ValidationError("La fecha de nacimiento debe ser desde 1930.")
        if value > today:
            raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        user = self.context["request"].user
        cliente = Cliente.objects.filter(credencial__usuario=user).first()

        correo_en_uso = (
            User.objects.exclude(pk=user.pk).filter(
                username__iexact=value
            ).exists()
            or User.objects.exclude(pk=user.pk).filter(email__iexact=value).exists()
            or Cliente.objects.exclude(pk=cliente.pk if cliente else None).filter(
                correo_cliente__iexact=value
            ).exists()
        )
        if correo_en_uso:
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def validate(self, attrs):
        tiene_latitud = attrs.get("latitud") is not None
        tiene_longitud = attrs.get("longitud") is not None
        if tiene_latitud != tiene_longitud:
            raise serializers.ValidationError(
                {"latitud": "Envía latitud y longitud juntas."}
            )

        request = self.context["request"]
        cliente = Cliente.objects.filter(credencial__usuario=request.user).first()
        if cliente and (
            attrs["tipo_documento"] != cliente.tipo_documento
            or attrs["numero_documento"].strip() != cliente.numero_documento
        ):
            raise serializers.ValidationError(
                {"tipo_documento": "El tipo y número de documento no se pueden modificar."}
            )
        tipo = attrs["tipo_documento"]
        numero = attrs["numero_documento"].strip()
        duplicado = Cliente.objects.exclude(pk=cliente.pk if cliente else None).filter(
            tipo_documento=tipo, numero_documento=numero
        ).exists()
        if duplicado:
            raise serializers.ValidationError(
                {"numero_documento": "Este documento ya está registrado."}
            )
        attrs["numero_documento"] = numero
        return attrs

    @transaction.atomic
    def update(self, cliente, validated_data):
        user = cliente.credencial.usuario
        email = validated_data["email"]

        for field in (
            "nombres",
            "apellidos",
            "telefono_cliente",
            "extension_telefonica",
            "direccion_residencia",
            "referencia_direccion",
            "latitud",
            "longitud",
            "fecha_nacimiento",
        ):
            if field in validated_data:
                setattr(cliente, field, validated_data[field])
        cliente.correo_cliente = email
        cliente.save()

        user.email = email
        user.username = email
        user.first_name = cliente.nombres
        user.last_name = cliente.apellidos
        user.save(update_fields=["email", "username", "first_name", "last_name"])
        return cliente


class TeamMemberSerializer(serializers.ModelSerializer):
    rol = serializers.CharField(source="perfil_trabajador.rol", default="sin_rol")
    rol_display = serializers.CharField(
        source="perfil_trabajador.get_rol_display", default="Sin rol"
    )
    sede_id = serializers.IntegerField(
        source="perfil_trabajador.sede.id_sede", default=None, allow_null=True
    )
    sede_nombre = serializers.CharField(
        source="perfil_trabajador.sede.nombre_sede", default=None, allow_null=True
    )
    telefono = serializers.CharField(source="perfil_trabajador.telefono", default="")

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "rol", "rol_display", "sede_id", "sede_nombre", "telefono", "is_active",
        ]


class TeamMemberCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    rol = serializers.ChoiceField(choices=PerfilTrabajador.Rol.choices)
    sede_id = serializers.IntegerField(required=False, allow_null=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta registrada con este correo electrónico.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este nombre de usuario.")
        return value

    def validate_sede_id(self, value):
        if value is not None and not Sede.objects.filter(id_sede=value).exists():
            raise serializers.ValidationError("La sede especificada no existe.")
        return value

    def create(self, validated_data):
        rol = validated_data.pop("rol")
        sede_id = validated_data.pop("sede_id", None)
        telefono = validated_data.pop("telefono", "")
        password = validated_data.pop("password")
        with transaction.atomic():
            user = User.objects.create(
                **validated_data, is_staff=True, is_active=True
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            PerfilTrabajador.objects.create(
                usuario=user, rol=rol, sede_id=sede_id, telefono=telefono
            )
        return user


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "La contraseña actual no es correcta."}
            )
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas nuevas no coinciden."}
            )
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"new_password": error.messages})
        return attrs


class CustomerProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)
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

    def validate_nombres(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los nombres solo pueden contener letras.")
        return value

    def validate_apellidos(self, value):
        value = value.strip()
        if not re.fullmatch(r"[^\d\W]+(?: [^\d\W]+)*", value, re.UNICODE):
            raise serializers.ValidationError("Los apellidos solo pueden contener letras.")
        return value

    def validate_fecha_nacimiento(self, value):
        today = date.today()
        if value < date(1930, 1, 1):
            raise serializers.ValidationError("La fecha de nacimiento debe ser desde 1930.")
        if value > today:
            raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")
        return value
    

    def validate_email(self, value):
        value = value.strip().lower()
        user = self.context["request"].user
        cliente = Cliente.objects.filter(credencial__usuario=user).first()

        correo_en_uso = (
            User.objects.exclude(pk=user.pk).filter(
                username__iexact=value
            ).exists()
            or User.objects.exclude(pk=user.pk).filter(email__iexact=value).exists()
            or Cliente.objects.exclude(pk=cliente.pk if cliente else None).filter(
                correo_cliente__iexact=value
            ).exists()
        )
        if correo_en_uso:
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def validate(self, attrs):
        tiene_latitud = attrs.get("latitud") is not None
        tiene_longitud = attrs.get("longitud") is not None
        if tiene_latitud != tiene_longitud:
            raise serializers.ValidationError(
                {"latitud": "Envía latitud y longitud juntas."}
            )

        request = self.context["request"]
        cliente = Cliente.objects.filter(credencial__usuario=request.user).first()
        if cliente and (
            attrs["tipo_documento"] != cliente.tipo_documento
            or attrs["numero_documento"].strip() != cliente.numero_documento
        ):
            raise serializers.ValidationError(
                {"tipo_documento": "El tipo y número de documento no se pueden modificar."}
            )
        tipo = attrs["tipo_documento"]
        numero = attrs["numero_documento"].strip()
        duplicado = Cliente.objects.exclude(pk=cliente.pk if cliente else None).filter(
            tipo_documento=tipo, numero_documento=numero
        ).exists()
        if duplicado:
            raise serializers.ValidationError(
                {"numero_documento": "Este documento ya está registrado."}
            )
        attrs["numero_documento"] = numero
        return attrs

    @transaction.atomic
    def update(self, cliente, validated_data):
        user = cliente.credencial.usuario
        email = validated_data["email"]

        for field in (
            "nombres",
            "apellidos",
            "telefono_cliente",
            "extension_telefonica",
            "direccion_residencia",
            "referencia_direccion",
            "latitud",
            "longitud",
            "fecha_nacimiento",
        ):
            if field in validated_data:
                setattr(cliente, field, validated_data[field])
        cliente.correo_cliente = email
        cliente.save()

        user.email = email
        user.username = email
        user.first_name = cliente.nombres
        user.last_name = cliente.apellidos
        user.save(update_fields=["email", "username", "first_name", "last_name"])
        return cliente



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = role_of(user)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": role_of(self.user),
            "sede": branch_of(self.user),
            "can_manage_menu": role_of(self.user) in {"operator", "admin"},
        }
        return data


class ItemCarritoSerializer(serializers.ModelSerializer):
    """Línea individual del carrito de compras con subtotal calculado (HU-C2)."""

    producto_id = serializers.IntegerField(source="producto.id_producto", read_only=True)
    nombre_producto = serializers.CharField(
        source="producto.nombre_producto", read_only=True
    )
    precio_unitario = serializers.DecimalField(
        source="producto.precio_venta",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    imagen_url = serializers.URLField(source="producto.imagen_url", read_only=True)
    subtotal_linea = serializers.SerializerMethodField()

    class Meta:
        model = ItemCarrito
        fields = [
            "id",
            "producto_id",
            "nombre_producto",
            "precio_unitario",
            "cantidad",
            "subtotal_linea",
            "imagen_url",
        ]

    def get_subtotal_linea(self, obj) -> str:
        return f"{obj.producto.precio_venta * obj.cantidad:.2f}"


class CarritoSerializer(serializers.ModelSerializer):
    """Carrito completo del cliente con totales recalculados automáticamente (HU-C2)."""

    items = ItemCarritoSerializer(many=True, read_only=True)
    sede_nombre = serializers.CharField(
        source="sede.nombre_sede", read_only=True, default=None
    )
    total_unidades = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    domicilio = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Carrito
        fields = [
            "id",
            "sede",
            "sede_nombre",
            "items",
            "total_unidades",
            "subtotal",
            "domicilio",
            "total",
            "actualizado_en",
        ]

    def get_total_unidades(self, obj) -> int:
        return sum(item.cantidad for item in obj.items.all())

    def _subtotal_decimal(self, obj):
        return sum(
            (item.producto.precio_venta * item.cantidad for item in obj.items.all()),
            0,
        )

    def get_subtotal(self, obj) -> str:
        return f"{self._subtotal_decimal(obj):.2f}"

    def get_domicilio(self, obj) -> str:
        return "0.00"

    def get_total(self, obj) -> str:
        return f"{self._subtotal_decimal(obj):.2f}"


class CarritoAddItemSerializer(serializers.Serializer):
    """Valida la adición de un producto al carrito y su disponibilidad en sede (HU-C2, HU-B14)."""

    producto_id = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1, max_value=20, default=1)
    sede_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    def validate(self, attrs):
        carrito = self.context["carrito"]
        producto_id = attrs["producto_id"]
        cantidad = attrs["cantidad"]

        try:
            producto = Producto.objects.select_related("categoria", "sede").get(
                pk=producto_id
            )
        except Producto.DoesNotExist:
            raise serializers.ValidationError({"producto_id": "El producto no existe."})

        if not producto.activo or (
            producto.categoria_id and not producto.categoria.activo
        ):
            raise serializers.ValidationError(
                {"producto_id": "Este producto no está disponible en el menú."}
            )

        sede_id = attrs.get("sede_id") or producto.sede_id or carrito.sede_id
        if not sede_id:
            raise serializers.ValidationError(
                {"sede_id": "Debes indicar la sede para agregar este producto."}
            )

        try:
            sede = Sede.objects.get(pk=sede_id)
        except Sede.DoesNotExist:
            raise serializers.ValidationError({"sede_id": "La sede indicada no existe."})

        from .catalog_views import in_branch, public_products

        if not in_branch(public_products(), sede.pk).filter(pk=producto.pk).exists():
            raise serializers.ValidationError(
                {"producto_id": "Este producto no pertenece a la sede seleccionada."}
            )

        if carrito.items.exists() and carrito.sede_id and carrito.sede_id != sede.pk:
            raise serializers.ValidationError(
                {
                    "sede_id": (
                        "Tu carrito contiene productos de otra sede. "
                        "Vacíalo antes de cambiar de sede."
                    )
                }
            )

        existing = carrito.items.filter(producto=producto).first()
        nueva_cantidad = (existing.cantidad if existing else 0) + cantidad
        if nueva_cantidad > 20:
            raise serializers.ValidationError(
                {"cantidad": "No puedes agregar más de 20 unidades de un mismo producto."}
            )

        inv = Inventario.objects.filter(producto=producto, sede=sede).first()
        if inv is not None:
            if inv.cantidad_disponible <= 0:
                raise serializers.ValidationError(
                    {"producto_id": "Este producto está agotado en la sede seleccionada."}
                )
            if nueva_cantidad > inv.cantidad_disponible:
                raise serializers.ValidationError(
                    {
                        "cantidad": (
                            f"Solo hay {inv.cantidad_disponible} unidades disponibles "
                            "en esta sede."
                        )
                    }
                )

        attrs["producto"] = producto
        attrs["sede"] = sede
        return attrs


class CarritoUpdateItemSerializer(serializers.Serializer):
    """Valida la actualización directa de la cantidad de un ítem en el carrito (HU-C2)."""

    cantidad = serializers.IntegerField(min_value=0, max_value=20)