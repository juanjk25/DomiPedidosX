from rest_framework import serializers

from .models import Inventario, Producto, Sede
from .permissions import branch_of, role_of


class InventorySerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    sede = serializers.PrimaryKeyRelatedField(
        queryset=Sede.objects.all(),
        required=False,
    )
    cantidad_disponible = serializers.IntegerField(min_value=0, default=0)
    stock_minimo = serializers.IntegerField(min_value=0, default=10)
    stock_maximo = serializers.IntegerField(min_value=1, default=1000)

    producto_nombre = serializers.CharField(
        source="producto.nombre_producto", read_only=True
    )
    codigo_de_barras = serializers.CharField(
        source="producto.codigo_de_barras", read_only=True
    )
    tipo_de_producto = serializers.SerializerMethodField()
    sede_nombre = serializers.CharField(source="sede.nombre_sede", read_only=True)
    stock_bajo = serializers.SerializerMethodField()

    class Meta:
        model = Inventario
        fields = [
            "id_inventario",
            "producto",
            "producto_nombre",
            "codigo_de_barras",
            "tipo_de_producto",
            "sede",
            "sede_nombre",
            "cantidad_disponible",
            "stock_minimo",
            "stock_maximo",
            "stock_bajo",
            "activo",
        ]
        validators = []
        extra_kwargs = {
            "activo": {"default": True},
        }

    def get_tipo_de_producto(self, obj):
        producto = obj.producto
        if producto.categoria_id:
            return producto.categoria.nombre
        return producto.tipo_de_producto

    def get_stock_bajo(self, obj):
        return obj.cantidad_disponible <= obj.stock_minimo

    def validate(self, attrs):
        user = self.context["request"].user
        instance = self.instance
        user_role = role_of(user)
        user_branch_id = branch_of(user)

        # Permitir deshabilitar un registro existente sin revalidar todo el objeto.
        only_deactivate = instance is not None and attrs == {"activo": False}

        if instance is None:
            if user_role == "operator":
                if user_branch_id is None:
                    raise serializers.ValidationError(
                        {"sede": "No tienes una sede asignada."}
                    )
                if "sede" not in attrs or attrs["sede"] is None:
                    attrs["sede"] = Sede.objects.get(pk=user_branch_id)
                elif attrs["sede"].pk != user_branch_id:
                    raise serializers.ValidationError(
                        {"sede": "Solo puedes gestionar el inventario de tu sede asignada."}
                    )
            elif not attrs.get("sede"):
                raise serializers.ValidationError(
                    {"sede": "Este campo es obligatorio."}
                )
        else:
            if user_role == "operator" and instance.sede_id != user_branch_id:
                raise serializers.ValidationError(
                    {"sede": "Solo puedes gestionar el inventario de tu sede asignada."}
                )
            if "sede" in attrs and attrs["sede"].pk != instance.sede_id:
                raise serializers.ValidationError(
                    {"sede": "No se puede trasladar un registro de inventario a otra sede."}
                )
            if "producto" in attrs and attrs["producto"].pk != instance.producto_id:
                raise serializers.ValidationError(
                    {"producto": "No se puede cambiar el producto de un inventario existente."}
                )

        if only_deactivate:
            return attrs

        sede = attrs.get("sede", getattr(instance, "sede", None))
        producto = attrs.get("producto", getattr(instance, "producto", None))

        errors = {}

        if instance is None and producto is not None:
            if not producto.activo:
                errors["producto"] = "Selecciona un producto activo."
            if producto.sede_id and sede and producto.sede_id != sede.pk:
                errors["producto"] = "El producto debe pertenecer a la sede seleccionada."

        if producto and sede:
            duplicate_qs = Inventario.objects.filter(producto=producto, sede=sede)
            if instance is not None:
                duplicate_qs = duplicate_qs.exclude(pk=instance.pk)
            if duplicate_qs.exists():
                errors["producto"] = (
                    "Ya existe un registro de inventario para este producto en esta sede."
                )

        cantidad = attrs.get(
            "cantidad_disponible", getattr(instance, "cantidad_disponible", 0)
        )
        stock_minimo = attrs.get(
            "stock_minimo", getattr(instance, "stock_minimo", 10)
        )
        stock_maximo = attrs.get(
            "stock_maximo", getattr(instance, "stock_maximo", 1000)
        )

        if stock_minimo > stock_maximo:
            errors["stock_minimo"] = (
                "El stock mínimo no puede ser mayor que el stock máximo."
            )
        if cantidad > stock_maximo:
            errors["cantidad_disponible"] = (
                "La cantidad disponible no puede superar el stock máximo."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class InventoryDisableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventario
        fields = ["id_inventario", "activo"]
        read_only_fields = ["id_inventario", "activo"]