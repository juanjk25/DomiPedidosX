from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import (
    Categoria,
    Ciudad,
    Departamento,
    Inventario,
    PerfilTrabajador,
    Producto,
    Sede,
)

User = get_user_model()


class InventoryEndpointsTests(APITestCase):
    def setUp(self):
        self.departamento = Departamento.objects.create(
            nombre_departamento="Valle del Cauca"
        )
        self.ciudad = Ciudad.objects.create(
            nombre_ciudad="Cali",
            departamento=self.departamento,
        )
        self.sede_norte = Sede.objects.create(
            nombre_sede="Sede Norte",
            barrio_sede="Granada",
            ciudad=self.ciudad,
            direccion="Calle 10 # 1-10",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )
        self.sede_sur = Sede.objects.create(
            nombre_sede="Sede Sur",
            barrio_sede="Ciudad Jardín",
            ciudad=self.ciudad,
            direccion="Calle 18 # 105-20",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )

        self.categoria_norte = Categoria.objects.create(
            nombre="Hamburguesas",
            sede=self.sede_norte,
            activo=True,
        )
        self.categoria_sur = Categoria.objects.create(
            nombre="Bebidas",
            sede=self.sede_sur,
            activo=True,
        )

        self.producto_norte = Producto.objects.create(
            codigo_de_barras="770000000001",
            nombre_producto="Hamburguesa Clásica",
            tipo_de_producto="Hamburguesas",
            activo=True,
            precio_compra=Decimal("10000.00"),
            precio_venta=Decimal("22000.00"),
            categoria=self.categoria_norte,
            sede=self.sede_norte,
            imagen_url="https://example.com/burger.jpg",
            tiempo_preparacion=15,
        )
        self.producto_norte_2 = Producto.objects.create(
            codigo_de_barras="770000000002",
            nombre_producto="Papas Fritas",
            tipo_de_producto="Hamburguesas",
            activo=True,
            precio_compra=Decimal("3000.00"),
            precio_venta=Decimal("8000.00"),
            categoria=self.categoria_norte,
            sede=self.sede_norte,
            imagen_url="https://example.com/fries.jpg",
            tiempo_preparacion=8,
        )
        self.producto_inactivo = Producto.objects.create(
            codigo_de_barras="770000000003",
            nombre_producto="Producto Descontinuado",
            tipo_de_producto="Hamburguesas",
            activo=False,
            precio_compra=Decimal("2000.00"),
            precio_venta=Decimal("5000.00"),
            categoria=self.categoria_norte,
            sede=self.sede_norte,
            imagen_url="https://example.com/old.jpg",
            tiempo_preparacion=5,
        )
        self.producto_sur = Producto.objects.create(
            codigo_de_barras="770000000004",
            nombre_producto="Limonada Natural",
            tipo_de_producto="Bebidas",
            activo=True,
            precio_compra=Decimal("2000.00"),
            precio_venta=Decimal("7000.00"),
            categoria=self.categoria_sur,
            sede=self.sede_sur,
            imagen_url="https://example.com/lemonade.jpg",
            tiempo_preparacion=5,
        )

        # Usuarios de prueba
        self.operator = User.objects.create_user(
            username="operador_norte",
            email="operador@domipedidos.test",
            password="Password123!",
            is_staff=True,
        )
        PerfilTrabajador.objects.create(
            usuario=self.operator,
            rol=PerfilTrabajador.Rol.OPERADOR,
            sede=self.sede_norte,
        )

        self.kitchen = User.objects.create_user(
            username="cocina_norte",
            email="cocina@domipedidos.test",
            password="Password123!",
            is_staff=True,
        )
        PerfilTrabajador.objects.create(
            usuario=self.kitchen,
            rol=PerfilTrabajador.Rol.COCINA,
            sede=self.sede_norte,
        )

        self.admin = User.objects.create_superuser(
            username="admin_test",
            email="admin@domipedidos.test",
            password="Password123!",
        )

        self.list_create_url = reverse("managed-inventory")

    def test_operator_can_create_inventory_auto_assigning_branch(self):
        self.client.force_authenticate(user=self.operator)
        payload = {
            "producto": self.producto_norte.pk,
            "cantidad_disponible": 25,
            "stock_minimo": 10,
            "stock_maximo": 100,
        }

        response = self.client.post(self.list_create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sede"], self.sede_norte.pk)
        self.assertEqual(response.data["cantidad_disponible"], 25)
        self.assertTrue(response.data["activo"])
        self.assertFalse(response.data["stock_bajo"])

    def test_operator_cannot_create_inventory_for_other_branch(self):
        self.client.force_authenticate(user=self.operator)
        payload = {
            "producto": self.producto_sur.pk,
            "sede": self.sede_sur.pk,
            "cantidad_disponible": 15,
            "stock_minimo": 5,
            "stock_maximo": 50,
        }

        response = self.client.post(self.list_create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sede", response.data)

    def test_cannot_create_duplicate_inventory_for_same_product_and_branch(self):
        Inventario.objects.create(
            producto=self.producto_norte,
            sede=self.sede_norte,
            cantidad_disponible=20,
            stock_minimo=5,
            stock_maximo=100,
        )
        self.client.force_authenticate(user=self.operator)

        response = self.client.post(
            self.list_create_url,
            {
                "producto": self.producto_norte.pk,
                "cantidad_disponible": 30,
                "stock_minimo": 5,
                "stock_maximo": 100,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("producto", response.data)

    def test_rejects_invalid_stock_ranges_and_inactive_product(self):
        self.client.force_authenticate(user=self.operator)

        resp_ranges = self.client.post(
            self.list_create_url,
            {
                "producto": self.producto_norte.pk,
                "cantidad_disponible": 120,
                "stock_minimo": 80,
                "stock_maximo": 50,
            },
            format="json",
        )
        self.assertEqual(resp_ranges.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stock_minimo", resp_ranges.data)
        self.assertIn("cantidad_disponible", resp_ranges.data)

        resp_inactive = self.client.post(
            self.list_create_url,
            {
                "producto": self.producto_inactivo.pk,
                "cantidad_disponible": 10,
                "stock_minimo": 5,
                "stock_maximo": 50,
            },
            format="json",
        )
        self.assertEqual(resp_inactive.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("producto", resp_inactive.data)

    def test_permissions_block_anonymous_and_kitchen_users(self):
        resp_anon = self.client.get(self.list_create_url)
        self.assertEqual(resp_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.kitchen)
        resp_kitchen = self.client.get(self.list_create_url)
        self.assertEqual(resp_kitchen.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_lists_only_own_branch_and_can_filter(self):
        inv_low = Inventario.objects.create(
            producto=self.producto_norte,
            sede=self.sede_norte,
            cantidad_disponible=5,
            stock_minimo=10,
            stock_maximo=100,
            activo=True,
        )
        inv_inactive = Inventario.objects.create(
            producto=self.producto_norte_2,
            sede=self.sede_norte,
            cantidad_disponible=50,
            stock_minimo=10,
            stock_maximo=100,
            activo=False,
        )
        Inventario.objects.create(
            producto=self.producto_sur,
            sede=self.sede_sur,
            cantidad_disponible=40,
            stock_minimo=10,
            stock_maximo=100,
            activo=True,
        )

        self.client.force_authenticate(user=self.operator)

        # Solo ve su sede (2 registros, excluye Sede Sur)
        resp_all = self.client.get(self.list_create_url)
        self.assertEqual(resp_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_all.data), 2)

        # Filtro por activo=true
        resp_active = self.client.get(f"{self.list_create_url}?activo=true")
        self.assertEqual(len(resp_active.data), 1)
        self.assertEqual(resp_active.data[0]["id_inventario"], inv_low.pk)

        # Filtro por stock_bajo=true
        resp_low = self.client.get(f"{self.list_create_url}?stock_bajo=true")
        self.assertEqual(len(resp_low.data), 1)
        self.assertTrue(resp_low.data[0]["stock_bajo"])

        # Búsqueda por nombre
        resp_search = self.client.get(f"{self.list_create_url}?search=Papas")
        self.assertEqual(len(resp_search.data), 1)
        self.assertEqual(resp_search.data[0]["id_inventario"], inv_inactive.pk)

    def test_admin_can_list_all_branches_and_filter_by_sede(self):
        Inventario.objects.create(
            producto=self.producto_norte,
            sede=self.sede_norte,
            cantidad_disponible=20,
        )
        inv_sur = Inventario.objects.create(
            producto=self.producto_sur,
            sede=self.sede_sur,
            cantidad_disponible=30,
        )

        self.client.force_authenticate(user=self.admin)

        resp_all = self.client.get(self.list_create_url)
        self.assertEqual(resp_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_all.data), 2)

        resp_sur = self.client.get(f"{self.list_create_url}?sede={self.sede_sur.pk}")
        self.assertEqual(len(resp_sur.data), 1)
        self.assertEqual(resp_sur.data[0]["id_inventario"], inv_sur.pk)

    def test_operator_can_disable_own_inventory_and_rejects_already_disabled(self):
        inventario = Inventario.objects.create(
            producto=self.producto_norte,
            sede=self.sede_norte,
            cantidad_disponible=15,
            activo=True,
        )
        disable_url = reverse(
            "managed-inventory-disable", kwargs={"pk": inventario.pk}
        )
        self.client.force_authenticate(user=self.operator)

        resp_first = self.client.patch(disable_url)
        self.assertEqual(resp_first.status_code, status.HTTP_200_OK)
        inventario.refresh_from_db()
        self.assertFalse(inventario.activo)

        resp_second = self.client.patch(disable_url)
        self.assertEqual(resp_second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_operator_cannot_disable_inventory_from_other_branch(self):
        inv_sur = Inventario.objects.create(
            producto=self.producto_sur,
            sede=self.sede_sur,
            cantidad_disponible=15,
            activo=True,
        )
        disable_url = reverse(
            "managed-inventory-disable", kwargs={"pk": inv_sur.pk}
        )
        self.client.force_authenticate(user=self.operator)

        response = self.client.patch(disable_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        inv_sur.refresh_from_db()
        self.assertTrue(inv_sur.activo)