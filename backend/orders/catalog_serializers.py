from decimal import Decimal
from urllib.parse import urlsplit

from django.db import transaction
from rest_framework import serializers

from .models import Categoria, Inventario, Producto, Sede
from .permissions import branch_of, role_of


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "descripcion", "sede", "activo"]


class MenuProductSerializer(serializers.ModelSerializer):
    # Se mantiene el nombre usado por los filtros del frontend existente.
    tipo_de_producto = serializers.SerializerMethodField()
    stock_disponible = serializers.SerializerMethodField()
    agotado = serializers.SerializerMethodField()

    def get_tipo_de_producto(self, obj) -> str:
        return obj.categoria.nombre if obj.categoria_id else obj.tipo_de_producto

    def _inventario_sede(self, obj):
        request = self.context.get("request")
        sede_id = None
        if request is not None:
            raw = request.query_params.get("sede", request.query_params.get("branch"))
            try:
                if raw and int(raw) > 0:
                    sede_id = int(raw)
            except (TypeError, ValueError):
                sede_id = None
        if sede_id is None:
            sede_id = obj.sede_id
        if sede_id is None:
            return None
        return obj.inventarios.filter(sede_id=sede_id).first()

    def get_stock_disponible(self, obj):
        inv = self._inventario_sede(obj)
        return inv.cantidad_disponible if inv is not None else None

    def get_agotado(self, obj) -> bool:
        inv = self._inventario_sede(obj)
        return inv.esta_agotado if inv is not None else False

    class Meta:
        model = Producto
        fields = [
            "id_producto",
            "codigo_de_barras",
            "nombre_producto",
            "tipo_de_producto",
            "categoria",
            "sede",
            "activo",
            "precio_venta",
            "imagen_url",
            "tiempo_preparacion",
            "stock_disponible",
            "agotado",
        ]


class InventarioAlertaSerializer(serializers.ModelSerializer):
    """Alerta de stock bajo o agotado para el operador de sede (HU-B14)."""

    producto_id = serializers.IntegerField(source="producto.id_producto", read_only=True)
    nombre_producto = serializers.CharField(source="producto.nombre_producto", read_only=True)
    sede_id = serializers.IntegerField(source="sede.id_sede", read_only=True)
    nombre_sede = serializers.CharField(source="sede.nombre_sede", read_only=True)
    nivel = serializers.CharField(source="nivel_alerta", read_only=True)

    class Meta:
        model = Inventario
        fields = [
            "id_inventario",
            "producto_id",
            "nombre_producto",
            "sede_id",
            "nombre_sede",
            "cantidad_disponible",
            "stock_minimo",
            "nivel",
        ]


class ManagedProductSerializer(MenuProductSerializer):
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())
    sede = serializers.PrimaryKeyRelatedField(queryset=Sede.objects.all())
    imagen_url = serializers.URLField(max_length=500)
    tiempo_preparacion = serializers.IntegerField(min_value=1, max_value=1440)
    precio_venta = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    precio_compra = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"), default=0
    )

    class Meta(MenuProductSerializer.Meta):
        fields = MenuProductSerializer.Meta.fields + ["precio_compra"]
        extra_kwargs = {"activo": {"default": True}}

    def validate_imagen_url(self, value):
        if urlsplit(value).scheme not in {"http", "https"}:
            raise serializers.ValidationError("Usa una URL de imagen HTTP o HTTPS.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        instance = self.instance
        # Desactivar un registro antiguo debe funcionar aunque aún no tenga imagen.
        only_deactivate = instance is not None and attrs == {"activo": False}
        if not only_deactivate:
            errors = {}
            for field in (
                "nombre_producto",
                "codigo_de_barras",
                "categoria",
                "sede",
                "imagen_url",
                "tiempo_preparacion",
            ):
                value = attrs.get(field, getattr(instance, field, None))
                if value is None or value == "":
                    errors[field] = "Este campo es obligatorio."
            category = attrs.get("categoria", getattr(instance, "categoria", None))
            sede = attrs.get("sede", getattr(instance, "sede", None))
            if category and not category.activo:
                errors["categoria"] = "Selecciona una categoría activa."
            if category and sede and category.sede_id != sede.pk:
                errors["categoria"] = "La categoría debe pertenecer a la sede del producto."
            if errors:
                raise serializers.ValidationError(errors)

        sede = attrs.get("sede", getattr(instance, "sede", None))
        if role_of(user) == "operator" and (not sede or sede.pk != branch_of(user)):
            raise serializers.ValidationError({"sede": "Solo puedes gestionar tu sede asignada."})
        if instance and "sede" in attrs and instance.sede_id and attrs["sede"].pk != instance.sede_id:
            raise serializers.ValidationError(
                {"sede": "No se puede trasladar un producto existente a otra sede."}
            )
        if instance and "sede" in attrs and not instance.sede_id:
            legacy_branches = set(instance.inventarios.values_list("sede_id", flat=True))
            if legacy_branches - {attrs["sede"].pk}:
                raise serializers.ValidationError(
                    {
                        "sede": (
                            "El inventario anterior pertenece a otra sede o a varias. "
                            "Coordina su separación con el equipo antes de asignar el producto."
                        )
                    }
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data["tipo_de_producto"] = validated_data["categoria"].nombre
        product = super().create(validated_data)
        Inventario.objects.get_or_create(producto=product, sede=product.sede)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        if "categoria" in validated_data:
            validated_data["tipo_de_producto"] = validated_data["categoria"].nombre
        product = super().update(instance, validated_data)
        if product.sede_id:
            Inventario.objects.get_or_create(producto=product, sede=product.sede)
        return product