from django.conf import settings
from django.db import models


class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    nombre_departamento = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "departamentos"


class Ciudad(models.Model):
    id_ciudad = models.BigAutoField(primary_key=True)
    nombre_ciudad = models.CharField(max_length=50, unique=True)
    departamento = models.ForeignKey(
        Departamento,
        db_column="id_departamento",
        on_delete=models.PROTECT,
        related_name="ciudades",
    )

    class Meta:
        db_table = "ciudad"


class Cliente(models.Model):
    id_cliente = models.BigAutoField(primary_key=True)
    tipo_documento = models.CharField(
        max_length=5,
        choices=(("CC", "CC"), ("CE", "CE"), ("NIT", "NIT"), ("TI", "TI")),
    )
    numero_documento = models.CharField(max_length=20)
    nombres = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    telefono_cliente = models.CharField(max_length=15, blank=True)
    extension_telefonica = models.CharField(max_length=10, blank=True)
    correo_cliente = models.EmailField(max_length=100, unique=True)
    direccion_residencia = models.CharField(max_length=150, blank=True)
    referencia_direccion = models.CharField(max_length=150, blank=True)
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    fecha_nacimiento = models.DateField()

    class Meta:
        db_table = "cliente"
        constraints = [
            models.UniqueConstraint(
                fields=("tipo_documento", "numero_documento"),
                name="uq_documento_cliente",
            )
        ]

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()


class CredencialCliente(models.Model):
    cliente = models.OneToOneField(
        Cliente, on_delete=models.CASCADE, related_name="credencial"
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cliente_credencial",
    )

    class Meta:
        db_table = "cliente_credencial"


class Sede(models.Model):
    id_sede = models.AutoField(primary_key=True)
    nombre_sede = models.CharField(max_length=50)
    barrio_sede = models.CharField(max_length=50)
    ciudad = models.ForeignKey(
        Ciudad, db_column="id_ciudad", on_delete=models.PROTECT, related_name="sedes"
    )
    direccion = models.CharField(max_length=100, unique=True)
    horario_atencion_apertura = models.TimeField()
    horario_atencion_cierre = models.TimeField()

    class Meta:
        db_table = "sedes"

    def esta_en_horario(self, hora_consulta=None):
        """
        Determina si la sede está abierta en una hora específica o en la hora actual.
        Útil para validaciones de disponibilidad al recibir pedidos (HU-E8).
        """
        from django.utils import timezone
        if hora_consulta is None:
            hora_consulta = timezone.localtime().time()

        if self.horario_atencion_apertura <= self.horario_atencion_cierre:
            return self.horario_atencion_apertura <= hora_consulta <= self.horario_atencion_cierre
        return (
            hora_consulta >= self.horario_atencion_apertura
            or hora_consulta <= self.horario_atencion_cierre
        )


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    activa = models.BooleanField(default=True) # El estado es global

    class Meta:
        db_table = "categorias"

class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    codigo_de_barras = models.CharField(max_length=30, unique=True)
    nombre_producto = models.CharField(max_length=80)
    categoria = models.ForeignKey(Categoria, db_column="id_categoria", on_delete=models.PROTECT, null=True)    
    activo = models.BooleanField(default=True)
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "productos"


class Inventario(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    producto = models.ForeignKey(
        Producto,
        db_column="id_producto",
        on_delete=models.PROTECT,
        related_name="inventarios",
    )
    sede = models.ForeignKey(Sede, db_column="id_sede", on_delete=models.PROTECT)
    cantidad_disponible = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=10)
    stock_maximo = models.IntegerField(default=1000)

    class Meta:
        db_table = "inventario"
        constraints = [
            models.UniqueConstraint(
                fields=("producto", "sede"), name="uq_inventario_producto_sede"
            )
        ]


class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    cedula_empleado = models.CharField(max_length=20, unique=True)
    nombre_empleado = models.CharField(max_length=50)
    apellido_empleado = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField()
    cargo = models.CharField(max_length=30)
    salario = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_contrato = models.DateField(auto_now_add=True)
    telefono_empleado = models.CharField(max_length=15, blank=True)
    correo_empleado = models.EmailField(max_length=100, unique=True, null=True)
    sede = models.ForeignKey(
        Sede, db_column="id_sede", on_delete=models.PROTECT, related_name="empleados"
    )

    class Meta:
        db_table = "empleados"


class Administrador(models.Model):
    id_administrador = models.AutoField(primary_key=True)
    cedula_administrador = models.CharField(max_length=20, unique=True)
    nombre_administrador = models.CharField(max_length=50)
    apellido_administrador = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField()
    cargo = models.CharField(max_length=30)
    salario = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_contrato = models.DateField(auto_now_add=True)
    telefono_administrador = models.CharField(max_length=15, blank=True)
    correo_administrador = models.EmailField(max_length=100, unique=True, null=True)
    sede = models.ForeignKey(
        Sede,
        db_column="id_sede",
        on_delete=models.PROTECT,
        related_name="administradores",
    )

    class Meta:
        db_table = "administrador"


class Repartidor(models.Model):
    id_repartidor = models.AutoField(primary_key=True)
    cedula_repartidor = models.CharField(max_length=20, unique=True)
    nombre_repartidor = models.CharField(max_length=50)
    apellido_repartidor = models.CharField(max_length=50)
    telefono_repartidor = models.CharField(max_length=20, unique=True)
    tipo_vehiculo = models.CharField(max_length=30)
    placa_vehiculo = models.CharField(max_length=15)
    estado_operativo = models.CharField(max_length=20, default="Inactivo")
    ultima_actualizacion_gps = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "repartidor"


class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente, db_column="id_cliente", on_delete=models.PROTECT, related_name="pedidos"
    )
    sede = models.ForeignKey(
        Sede, db_column="id_sede", on_delete=models.PROTECT, related_name="pedidos"
    )
    repartidor = models.ForeignKey(
        Repartidor,
        db_column="id_repartidor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pedidos",
    )
    estado_pedido = models.CharField(max_length=30, default="Pendiente")
    direccion_entrega = models.CharField(max_length=150)
    notas_cliente = models.TextField(blank=True)
    fecha_hora_pedido = models.DateTimeField(auto_now_add=True)
    tiempo_estimado_entrega = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "pedido"
        ordering = ["-fecha_hora_pedido"]


class DetallePedido(models.Model):
    id_linea = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(
        Pedido, db_column="id_pedido", on_delete=models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        Producto, db_column="id_producto", on_delete=models.PROTECT
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario_aplicado = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal_linea = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    iva_aplicado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = "detalle_pedido"
        constraints = [
            models.UniqueConstraint(
                fields=("pedido", "producto"), name="uq_detalle_pedido_producto"
            )
        ]


class Factura(models.Model):
    id_factura = models.AutoField(primary_key=True)
    numero_factura_oficial = models.CharField(max_length=50, unique=True)
    pedido = models.OneToOneField(
        Pedido, db_column="id_pedido", on_delete=models.PROTECT, related_name="factura"
    )
    empleado = models.ForeignKey(
        Empleado, db_column="id_empleado", on_delete=models.PROTECT
    )
    fecha_emision = models.DateTimeField(auto_now_add=True)
    forma_pago = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    total_factura = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    cambio_devuelto = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = "factura"


class PerfilTrabajador(models.Model):
    """
    Perfil laboral asociado a una cuenta de usuario del sistema (HU-A9).
    Permite al administrador asignar y persistir el rol y la sede del trabajador.
    """

    class Rol(models.TextChoices):
        OPERADOR = "operador_sede", "Operador de sede"
        COCINA = "cocina", "Cocina"
        REPARTIDOR = "repartidor", "Repartidor"
        ADMINISTRADOR = "administrador", "Administrador"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_trabajador",
    )
    rol = models.CharField(max_length=20, choices=Rol.choices)
    sede = models.ForeignKey(
        Sede,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="trabajadores",
    )
    telefono = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "perfil_trabajador"

    def __str__(self):
        return f"{self.usuario.username} ({self.get_rol_display()})"
class CredencialEmpleado(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name="credencial")
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="empleado_credencial")

    class Meta:
        db_table = "empleado_credencial"
