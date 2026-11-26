from datetime import date, time
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import (
    Categoria,
    Ciudad,
    Cliente,
    CredencialCliente,
    Departamento,
    Inventario,
    Pedido,
    PerfilTrabajador,
    Producto,
    Sede,
)

User = get_user_model()


class Sprint2WilliamTests(APITestCase):
    """
    Pruebas unitarias para las historias del Sprint 2 asignadas a William David:
    - HU-B14: Bloqueo automático de productos agotados y alertas de stock por sede.
    - HU-C2: Actualizar carrito de compras con recálculo automático.
    - HU-C6: Función cancelar pedido (cliente, operador, admin) y salida de cocina.
    - HU-C7: Restringir cancelación cuando el pedido ya está en preparación.
    """

    def setUp(self):
        self.depto = Departamento.objects.create(nombre_departamento="Valle del Cauca")
        self.ciudad = Ciudad.objects.create(nombre_ciudad="Cali", departamento=self.depto)

        self.sede_norte = Sede.objects.create(
            nombre_sede="Sede Norte",
            barrio_sede="Granada",
            ciudad=self.ciudad,
            direccion="Av 9 # 10-20",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )
        self.sede_sur = Sede.objects.create(
            nombre_sede="Sede Sur",
            barrio_sede="Ciudad Jardín",
            ciudad=self.ciudad,
            direccion="Cra 100 # 15-30",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )

        self.cat_norte = Categoria.objects.create(
            nombre="Pizzas", descripcion="Pizzas artesanales", sede=self.sede_norte
        )
        self.cat_sur = Categoria.objects.create(
            nombre="Bebidas", descripcion="Bebidas frías", sede=self.sede_sur
        )

        self.pizza = Producto.objects.create(
            codigo_de_barras="PIZ-001",
            nombre_producto="Pizza Margarita",
            tipo_de_producto="Pizzas",
            precio_compra=Decimal("12000.00"),
            precio_venta=Decimal("25000.00"),
            categoria=self.cat_norte,
            sede=self.sede_norte,
            imagen_url="https://example.com/pizza.jpg",
            tiempo_preparacion=20,
        )
        self.gaseosa = Producto.objects.create(
            codigo_de_barras="BEB-001",
            nombre_producto="Gaseosa 1.5L",
            tipo_de_producto="Pizzas",
            precio_compra=Decimal("3000.00"),
            precio_venta=Decimal("7000.00"),
            categoria=self.cat_norte,
            sede=self.sede_norte,
            imagen_url="https://example.com/gaseosa.jpg",
            tiempo_preparacion=2,
        )
        self.jugo_sur = Producto.objects.create(
            codigo_de_barras="JUG-001",
            nombre_producto="Jugo Natural",
            tipo_de_producto="Bebidas",
            precio_compra=Decimal("3000.00"),
            precio_venta=Decimal("8000.00"),
            categoria=self.cat_sur,
            sede=self.sede_sur,
            imagen_url="https://example.com/jugo.jpg",
            tiempo_preparacion=5,
        )

        self.inv_pizza = Inventario.objects.create(
            producto=self.pizza,
            sede=self.sede_norte,
            cantidad_disponible=3,
            stock_minimo=5,
        )
        self.inv_gaseosa = Inventario.objects.create(
            producto=self.gaseosa,
            sede=self.sede_norte,
            cantidad_disponible=0,
            stock_minimo=5,
        )
        self.inv_jugo_sur = Inventario.objects.create(
            producto=self.jugo_sur,
            sede=self.sede_sur,
            cantidad_disponible=4,
            stock_minimo=2,
        )

        # Cliente
        self.cliente_user = User.objects.create_user(
            username="cliente@test.com",
            email="cliente@test.com",
            password="ClaveSegura123!",
        )
        self.cliente = Cliente.objects.create(
            tipo_documento="CC",
            numero_documento="12345678",
            nombres="Laura",
            apellidos="Gómez",
            telefono_cliente="3001112233",
            correo_cliente="cliente@test.com",
            direccion_residencia="Calle 10 # 20-30",
            fecha_nacimiento=date(1998, 5, 10),
        )
        CredencialCliente.objects.create(cliente=self.cliente, usuario=self.cliente_user)

        # Operador Norte, Operador Sur, Cocina Norte y Admin
        self.operador_norte = User.objects.create_user(
            username="op_norte", email="op_norte@test.com", password="Clave123!", is_staff=True
        )
        PerfilTrabajador.objects.create(
            usuario=self.operador_norte, rol="operador_sede", sede=self.sede_norte
        )

        self.operador_sur = User.objects.create_user(
            username="op_sur", email="op_sur@test.com", password="Clave123!", is_staff=True
        )
        PerfilTrabajador.objects.create(
            usuario=self.operador_sur, rol="operador_sede", sede=self.sede_sur
        )

        self.cocina_norte = User.objects.create_user(
            username="cocina_norte", email="cocina@test.com", password="Clave123!", is_staff=True
        )
        PerfilTrabajador.objects.create(
            usuario=self.cocina_norte, rol="cocina", sede=self.sede_norte
        )

        self.admin = User.objects.create_superuser(
            username="admin_s2", email="admin_s2@test.com", password="Clave123!"
        )

    # --- HU-B14 ---
    def test_producto_agotado_se_bloquea_en_pedido_y_carrito(self):
        self.client.force_authenticate(user=self.cliente_user)

        menu_resp = self.client.get(f"/api/products/?sede={self.sede_norte.pk}")
        self.assertEqual(menu_resp.status_code, status.HTTP_200_OK)
        by_id = {item["id_producto"]: item for item in menu_resp.data}
        self.assertTrue(by_id[self.gaseosa.pk]["agotado"])
        self.assertFalse(by_id[self.pizza.pk]["agotado"])

        cart_resp = self.client.post(
            "/api/cart/items/",
            {"producto_id": self.gaseosa.pk, "cantidad": 1},
            format="json",
        )
        self.assertEqual(cart_resp.status_code, status.HTTP_400_BAD_REQUEST)

        order_resp = self.client.post(
            "/api/orders/",
            {
                "sede": self.sede_norte.pk,
                "direccion_entrega": "Calle 10 # 20-30",
                "items": [{"producto_id": self.gaseosa.pk, "cantidad": 1}],
            },
            format="json",
        )
        self.assertEqual(order_resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pedido_descuenta_stock_y_bloquea_al_llegar_a_cero(self):
        self.client.force_authenticate(user=self.cliente_user)
        resp1 = self.client.post(
            "/api/orders/",
            {
                "sede": self.sede_norte.pk,
                "direccion_entrega": "Calle 10 # 20-30",
                "items": [{"producto_id": self.pizza.pk, "cantidad": 3}],
            },
            format="json",
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        self.inv_pizza.refresh_from_db()
        self.assertEqual(self.inv_pizza.cantidad_disponible, 0)
        self.assertTrue(self.inv_pizza.esta_agotado)

        resp2 = self.client.post(
            "/api/orders/",
            {
                "sede": self.sede_norte.pk,
                "direccion_entrega": "Calle 10 # 20-30",
                "items": [{"producto_id": self.pizza.pk, "cantidad": 1}],
            },
            format="json",
        )
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_alertas_inventario_corresponden_a_su_sede(self):
        self.client.force_authenticate(user=self.operador_norte)
        resp = self.client.get("/api/management/inventory/alerts/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        niveles = {item["producto_id"]: item["nivel"] for item in resp.data}
        self.assertEqual(niveles[self.gaseosa.pk], "agotado")
        self.assertEqual(niveles[self.pizza.pk], "stock_bajo")
        self.assertNotIn(self.jugo_sur.pk, niveles)

        # Operador sur no ve alertas porque su stock (4) > stock_minimo (2)
        self.client.force_authenticate(user=self.operador_sur)
        resp_sur = self.client.get("/api/management/inventory/alerts/")
        self.assertEqual(resp_sur.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_sur.data, [])

    # --- HU-C2 ---
    def test_agregar_producto_al_carrito_incrementa_y_recalcula_subtotal(self):
        self.client.force_authenticate(user=self.cliente_user)

        r1 = self.client.post(
            "/api/cart/items/",
            {"producto_id": self.pizza.pk, "cantidad": 1},
            format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r1.data["total_unidades"], 1)
        self.assertEqual(r1.data["subtotal"], "25000.00")

        # Agregar nuevamente el mismo producto incrementa su cantidad (1 + 2 = 3)
        r2 = self.client.post(
            "/api/cart/items/",
            {"producto_id": self.pizza.pk, "cantidad": 2},
            format="json",
        )
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r2.data["items"]), 1)
        self.assertEqual(r2.data["items"][0]["cantidad"], 3)
        self.assertEqual(r2.data["items"][0]["subtotal_linea"], "75000.00")
        self.assertEqual(r2.data["total_unidades"], 3)
        self.assertEqual(r2.data["subtotal"], "75000.00")
        self.assertEqual(r2.data["total"], "75000.00")

    def test_actualizar_cantidad_y_rechazar_mezcla_de_sedes_en_carrito(self):
        self.client.force_authenticate(user=self.cliente_user)
        self.client.post(
            "/api/cart/items/",
            {"producto_id": self.pizza.pk, "cantidad": 1},
            format="json",
        )

        # No permite mezclar producto de Sede Sur
        r_otra = self.client.post(
            "/api/cart/items/",
            {"producto_id": self.jugo_sur.pk, "cantidad": 1},
            format="json",
        )
        self.assertEqual(r_otra.status_code, status.HTTP_400_BAD_REQUEST)

        # No permite exceder stock disponible (3)
        r_exceso = self.client.patch(
            f"/api/cart/items/{self.pizza.pk}/",
            {"cantidad": 5},
            format="json",
        )
        self.assertEqual(r_exceso.status_code, status.HTTP_400_BAD_REQUEST)

        # Actualizar a cantidad válida recalcula
        r_ok = self.client.patch(
            f"/api/cart/items/{self.pizza.pk}/",
            {"cantidad": 2},
            format="json",
        )
        self.assertEqual(r_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(r_ok.data["subtotal"], "50000.00")

    # --- HU-C6 y HU-C7 ---
    def test_cancelar_pedido_pendiente_sale_de_cocina_y_restaura_stock(self):
        self.client.force_authenticate(user=self.cliente_user)
        order_resp = self.client.post(
            "/api/orders/",
            {
                "sede": self.sede_norte.pk,
                "direccion_entrega": "Calle 10 # 20-30",
                "items": [{"producto_id": self.pizza.pk, "cantidad": 2}],
            },
            format="json",
        )
        self.assertEqual(order_resp.status_code, status.HTTP_201_CREATED)
        pedido_id = order_resp.data["id_pedido"]

        self.inv_pizza.refresh_from_db()
        self.assertEqual(self.inv_pizza.cantidad_disponible, 1)

        # Cocina ve el pedido en recibidos antes de cancelar
        self.client.force_authenticate(user=self.cocina_norte)
        cocina_antes = self.client.get("/api/pedidos/cocina/")
        self.assertEqual(len(cocina_antes.data["pedidos_por_estado"]["recibidos"]), 1)

        # Cliente cancela el pedido
        self.client.force_authenticate(user=self.cliente_user)
        cancel_resp = self.client.post(f"/api/orders/{pedido_id}/cancel/")
        self.assertEqual(cancel_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_resp.data["estado_pedido"], "Cancelado")

        # Stock restaurado y cocina ya no lo visualiza
        self.inv_pizza.refresh_from_db()
        self.assertEqual(self.inv_pizza.cantidad_disponible, 3)

        self.client.force_authenticate(user=self.cocina_norte)
        cocina_despues = self.client.get("/api/pedidos/cocina/")
        self.assertEqual(len(cocina_despues.data["pedidos_por_estado"]["recibidos"]), 0)

    def test_operador_sede_puede_cancelar_y_otro_operador_no(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            sede=self.sede_norte,
            direccion_entrega="Calle 10 # 20-30",
            estado_pedido="Pendiente",
        )

        self.client.force_authenticate(user=self.operador_sur)
        r_otro = self.client.post(f"/api/orders/{pedido.pk}/cancel/")
        self.assertEqual(r_otro.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(user=self.operador_norte)
        r_ok = self.client.post(f"/api/orders/{pedido.pk}/cancel/")
        self.assertEqual(r_ok.status_code, status.HTTP_200_OK)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado_pedido, "Cancelado")

    def test_restringe_cancelacion_cuando_esta_en_preparacion_o_posterior(self):
        for estado in ["Preparando", "Listo", "En Camino", "Entregado"]:
            pedido = Pedido.objects.create(
                cliente=self.cliente,
                sede=self.sede_norte,
                direccion_entrega="Calle 10 # 20-30",
                estado_pedido=estado,
            )
            self.client.force_authenticate(user=self.cliente_user)
            resp = self.client.post(f"/api/orders/{pedido.pk}/cancel/")
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", resp.data)
            pedido.refresh_from_db()
            self.assertEqual(pedido.estado_pedido, estado)
