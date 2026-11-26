from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import (
    Administrador,
    Ciudad,
    Cliente,
    CredencialCliente,
    Departamento,
    DetallePedido,
    Empleado,
    Pedido,
    Producto,
    Sede,
)

User = get_user_model()


class KitchenOrderQueueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        department = Departamento.objects.create(
            nombre_departamento="Departamento de prueba"
        )
        city = Ciudad.objects.create(
            nombre_ciudad="Ciudad de prueba",
            departamento=department,
        )

        cls.branch = Sede.objects.create(
            nombre_sede="Sede Centro",
            barrio_sede="Centro",
            ciudad=city,
            direccion="Calle de prueba 1",
            horario_atencion_apertura="08:00",
            horario_atencion_cierre="22:00",
        )
        cls.other_branch = Sede.objects.create(
            nombre_sede="Sede Norte",
            barrio_sede="Norte",
            ciudad=city,
            direccion="Calle de prueba 2",
            horario_atencion_apertura="08:00",
            horario_atencion_cierre="22:00",
        )

        cls.customer = Cliente.objects.create(
            tipo_documento="CC",
            numero_documento="123456789",
            nombres="Cliente",
            apellidos="Prueba",
            correo_cliente="cliente@example.com",
            fecha_nacimiento="2000-01-01",
        )

        cls.product = Producto.objects.create(
            codigo_de_barras="PRODUCTO-001",
            nombre_producto="Pizza de prueba",
            tipo_de_producto="Comida",
            precio_compra="10000.00",
            precio_venta="20000.00",
        )

        cls.kitchen_user = User.objects.create_user(
            username="cocina@example.com",
            email="cocina@example.com",
            password="prueba-segura-123",
            is_staff=True,
        )
        Empleado.objects.create(
            cedula_empleado="100000001",
            nombre_empleado="Personal",
            apellido_empleado="Cocina",
            fecha_nacimiento="1995-01-01",
            cargo="Cocina",
            salario="1500000.00",
            correo_empleado="cocina@example.com",
            sede=cls.branch,
        )

        cls.operator_user = User.objects.create_user(
            username="operador@example.com",
            email="operador@example.com",
            password="prueba-segura-123",
            is_staff=True,
        )
        Empleado.objects.create(
            cedula_empleado="100000002",
            nombre_empleado="Personal",
            apellido_empleado="Operador",
            fecha_nacimiento="1995-01-01",
            cargo="Operador",
            salario="1500000.00",
            correo_empleado="operador@example.com",
            sede=cls.branch,
        )

        cls.customer_user = User.objects.create_user(
            username="cliente@example.com",
            email="cliente@example.com",
            password="prueba-segura-123",
        )
        CredencialCliente.objects.create(
            cliente=cls.customer,
            usuario=cls.customer_user,
        )

        cls.admin_user = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="prueba-segura-123",
        )

    def setUp(self):
        self.api = APIClient()
        self.url = "/api/pedidos/cocina/"

    def create_order(self, estado, sede=None, with_item=False):
        order = Pedido.objects.create(
            cliente=self.customer,
            sede=sede or self.branch,
            estado_pedido=estado,
            direccion_entrega="Dirección de prueba",
        )

        if with_item:
            DetallePedido.objects.create(
                pedido=order,
                producto=self.product,
                cantidad=2,
                precio_unitario_aplicado="20000.00",
            )

        return order

    def test_kitchen_orders_are_grouped_by_status(self):
        received = self.create_order("Pendiente", with_item=True)
        preparing = self.create_order("Preparando")
        ready = self.create_order("Listo")
        self.create_order("En Camino")
        self.create_order("Cancelado")

        self.api.force_authenticate(self.kitchen_user)
        response = self.api.get(self.url)

        self.assertEqual(response.status_code, 200, response.data)

        columns = response.data["pedidos_por_estado"]
        self.assertEqual(
            [order["id_pedido"] for order in columns["recibidos"]],
            [received.id_pedido],
        )
        self.assertEqual(
            [order["id_pedido"] for order in columns["en_preparacion"]],
            [preparing.id_pedido],
        )
        self.assertEqual(
            [order["id_pedido"] for order in columns["listos"]],
            [ready.id_pedido],
        )
        self.assertEqual(
            columns["recibidos"][0]["detalles"][0]["nombre_producto"],
            "Pizza de prueba",
        )

    def test_kitchen_user_only_sees_orders_from_their_branch(self):
        local_order = self.create_order("Pendiente", sede=self.branch)
        other_order = self.create_order("Pendiente", sede=self.other_branch)

        self.api.force_authenticate(self.kitchen_user)
        response = self.api.get(self.url)

        self.assertEqual(response.status_code, 200)

        received_orders = response.data["pedidos_por_estado"]["recibidos"]
        received_ids = [order["id_pedido"] for order in received_orders]

        self.assertIn(local_order.id_pedido, received_ids)
        self.assertNotIn(other_order.id_pedido, received_ids)

    def test_administrator_can_see_orders_from_all_branches(self):
        local_order = self.create_order("Pendiente", sede=self.branch)
        other_order = self.create_order("Pendiente", sede=self.other_branch)

        self.api.force_authenticate(self.admin_user)
        response = self.api.get(self.url)

        self.assertEqual(response.status_code, 200, response.data)

        received_orders = response.data["pedidos_por_estado"]["recibidos"]
        received_ids = [order["id_pedido"] for order in received_orders]

        self.assertCountEqual(
            received_ids,
            [local_order.id_pedido, other_order.id_pedido],
        )

    def test_operator_and_customer_are_denied(self):
        self.api.force_authenticate(self.operator_user)
        operator_response = self.api.get(self.url)
        self.assertEqual(operator_response.status_code, 403)

        self.api.force_authenticate(self.customer_user)
        customer_response = self.api.get(self.url)
        self.assertEqual(customer_response.status_code, 403)

    def test_anonymous_user_is_denied(self):
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_schema_and_swagger_pages_are_available(self):
        schema_response = APIClient().get("/api/schema/")
        swagger_response = APIClient().get("/api/docs/")

        self.assertEqual(schema_response.status_code, 200)
        self.assertIn(
            "/api/pedidos/cocina/",
            schema_response.content.decode(),
        )
        self.assertEqual(swagger_response.status_code, 200)