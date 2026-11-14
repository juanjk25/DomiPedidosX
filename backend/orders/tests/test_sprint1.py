from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from orders.models import (Categoria, Ciudad, Cliente, CredencialCliente, Departamento,
                           Inventario, Pedido, PerfilPersonal, Producto, Sede)

User = get_user_model()


class Sprint1Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dep = Departamento.objects.create(nombre_departamento='Prueba')
        city = Ciudad.objects.create(nombre_ciudad='Prueba', departamento=dep)
        cls.branch = Sede.objects.create(nombre_sede='Centro', barrio_sede='Centro', ciudad=city,
            direccion='Calle 1', horario_atencion_apertura='08:00', horario_atencion_cierre='22:00')
        cls.other = Sede.objects.create(nombre_sede='Norte', barrio_sede='Norte', ciudad=city,
            direccion='Calle 2', horario_atencion_apertura='08:00', horario_atencion_cierre='22:00')
        cls.category = Categoria.objects.create(nombre='Comida', sede=cls.branch, descripcion='Comidas de Centro')
        cls.inactive_category = Categoria.objects.create(nombre='Retirada', sede=cls.branch, activo=False)
        cls.other_category = Categoria.objects.create(nombre='Comida', sede=cls.other, descripcion='Comidas de Norte')
        cls.operator = User.objects.create_user('operador', password='ClavePrueba-489!', is_staff=True)
        PerfilPersonal.objects.create(usuario=cls.operator, rol='operator', sede=cls.branch)
        cls.kitchen = User.objects.create_user('cocina', is_staff=True)
        PerfilPersonal.objects.create(usuario=cls.kitchen, rol='kitchen', sede=cls.branch)
        cls.staff_without_profile = User.objects.create_user('sin-asignacion', is_staff=True)
        cls.admin = User.objects.create_superuser('admin', 'admin@example.org', 'ClavePrueba-489!')
        cls.customer = User.objects.create_user('cliente@example.org', 'cliente@example.org', 'ClavePrueba-489!')
        customer_profile = Cliente.objects.create(tipo_documento='CC', numero_documento='123', nombres='Cliente',
            apellidos='Prueba', correo_cliente='cliente@example.org', fecha_nacimiento='2000-01-01', direccion_residencia='Calle 3')
        CredencialCliente.objects.create(cliente=customer_profile, usuario=cls.customer)
        cls.product = Producto.objects.create(codigo_de_barras='001', nombre_producto='Pizza', categoria=cls.category,
            tipo_de_producto='Comida', sede=cls.branch, imagen_url='https://example.org/pizza.png', tiempo_preparacion=15,
            precio_compra=10000, precio_venta=20000)
        cls.other_product = Producto.objects.create(codigo_de_barras='002', nombre_producto='Pizza norte', categoria=cls.other_category,
            tipo_de_producto='Comida', sede=cls.other, imagen_url='https://example.org/pizza.png', tiempo_preparacion=15,
            precio_compra=10000, precio_venta=21000)
        Inventario.objects.create(producto=cls.product, sede=cls.branch, cantidad_disponible=10)

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(self.operator)
        self.url = f'/api/management/products/{self.product.pk}/'
        self.data = dict(codigo_de_barras='003', nombre_producto='Hamburguesa', categoria=self.category.pk,
            sede=self.branch.pk, imagen_url='https://example.org/burger.jpg', tiempo_preparacion=20,
            precio_venta='24000.50', precio_compra='12000.00', activo=True)

    def create(self, **changes):
        return self.api.post('/api/management/products/', {**self.data, **changes}, format='json')

    def test_create_persists_fields_and_branch_inventory(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        p = Producto.objects.get(pk=response.data['id_producto'])
        self.assertEqual(p.nombre_producto, 'Hamburguesa')
        self.assertEqual(p.precio_venta, Decimal('24000.50'))
        self.assertEqual(p.imagen_url, self.data['imagen_url'])
        self.assertEqual(p.tiempo_preparacion, 20)
        self.assertEqual(p.sede, self.branch)
        self.assertEqual(p.categoria, self.category)
        self.assertTrue(Inventario.objects.filter(producto=p, sede=self.branch).exists())

    def test_required_fields(self):
        for field in ['codigo_de_barras', 'nombre_producto', 'categoria', 'sede', 'imagen_url', 'tiempo_preparacion', 'precio_venta']:
            with self.subTest(field=field):
                data = self.data.copy(); del data[field]
                response = self.api.post('/api/management/products/', data, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
        self.assertEqual(Producto.objects.count(), 2)

    def test_whitespace_name_is_rejected(self):
        self.assertEqual(self.create(nombre_producto='   ').status_code, 400)

    def test_invalid_prices_minutes_and_images(self):
        for field, values in {'precio_venta': ['0', '-1', '1.234', '10000000000'], 'precio_compra': ['-1'],
                              'tiempo_preparacion': [0, -1, 1.5, 1441], 'imagen_url': ['texto', 'javascript:alert(1)', 'ftp://example.org/x']}.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    response = self.create(**{field: value})
                    self.assertEqual(response.status_code, 400, response.data)

    def test_duplicate_code_is_rejected(self):
        self.assertEqual(self.create(codigo_de_barras='001').status_code, 400)

    def test_inactive_or_nonexistent_category_rejected(self):
        for category in [self.inactive_category.pk, 987654]:
            self.assertEqual(self.create(categoria=category).status_code, 400)

    def test_edit_persists_and_public_api_reflects_changes(self):
        response = self.api.patch(self.url, {'nombre_producto': 'Pizza nueva', 'precio_venta': '29999.50', 'tiempo_preparacion': 25}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.precio_venta, Decimal('29999.50'))
        public = APIClient().get(f'/api/products/?sede={self.branch.pk}')
        self.assertEqual(public.data[0]['nombre_producto'], 'Pizza nueva')
        self.assertEqual(public.data[0]['tiempo_preparacion'], 25)

    def test_invalid_edit_leaves_database_unchanged(self):
        response = self.api.patch(self.url, {'nombre_producto': ''}, format='json')
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        self.assertEqual(self.product.nombre_producto, 'Pizza')

    def test_disable_soft_deletes_and_hides_from_customer(self):
        response = self.api.patch(self.url, {'activo': False}, format='json')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.activo)
        self.assertEqual(APIClient().get(f'/api/products/?sede={self.branch.pk}').data, [])
        managed = self.api.get('/api/management/products/').data
        self.assertEqual(len(managed), 1)
        self.assertFalse(managed[0]['activo'])
        self.assertTrue(Inventario.objects.filter(producto=self.product).exists())

    def test_disable_legacy_product_without_image(self):
        self.product.imagen_url = ''; self.product.tiempo_preparacion = None; self.product.save()
        self.assertEqual(self.api.patch(self.url, {'activo': False}, format='json').status_code, 200)

    def test_reactivate_product(self):
        self.product.activo = False; self.product.save()
        self.assertEqual(self.api.patch(self.url, {'activo': True}, format='json').status_code, 200)
        self.assertEqual(len(APIClient().get(f'/api/products/?sede={self.branch.pk}').data), 1)

    def test_operator_cannot_create_for_another_branch(self):
        self.assertEqual(self.create(sede=self.other.pk).status_code, 400)

    def test_operator_cannot_read_edit_or_disable_other_branch(self):
        url = f'/api/management/products/{self.other_product.pk}/'
        self.assertEqual(self.api.get(url).status_code, 404)
        self.assertEqual(self.api.patch(url, {'nombre_producto': 'Otro'}, format='json').status_code, 404)
        self.assertEqual(self.api.patch(url, {'activo': False}, format='json').status_code, 404)
        self.assertEqual(self.api.get(f'/api/management/products/?sede={self.other.pk}').data, [])

    def test_non_managers_cannot_manage(self):
        for user in [None, self.customer, self.kitchen, self.staff_without_profile]:
            with self.subTest(user=str(user)):
                self.api.force_authenticate(user)
                self.assertIn(self.api.get('/api/management/products/').status_code, [401, 403])
                self.assertIn(self.create().status_code, [401, 403])
                self.assertIn(self.api.patch(self.url, {'activo': False}, format='json').status_code, [401, 403])

    def test_staff_without_profile_does_not_become_admin(self):
        self.api.force_authenticate(self.staff_without_profile)
        self.assertFalse(self.api.get('/api/me/').data['can_manage_menu'])

    def test_admin_manages_both_branches(self):
        self.api.force_authenticate(self.admin)
        self.assertEqual(len(self.api.get('/api/management/products/').data), 2)
        self.assertEqual(self.create(sede=self.other.pk, categoria=self.other_category.pk).status_code, 201)

    def test_cannot_move_existing_product(self):
        self.api.force_authenticate(self.admin)
        self.assertEqual(self.api.patch(self.url, {'sede': self.other.pk}, format='json').status_code, 400)

    def test_operator_branch_list_is_scoped(self):
        branches = self.api.get('/api/management/branches/').data
        self.assertEqual([b['id_sede'] for b in branches], [self.branch.pk])

    def test_shared_legacy_product_cannot_be_silently_reassigned(self):
        self.product.sede = None
        self.product.save()
        Inventario.objects.create(producto=self.product, sede=self.other)
        self.api.force_authenticate(self.admin)
        response = self.api.patch(self.url, {'sede': self.branch.pk}, format='json')
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        self.assertIsNone(self.product.sede)

    def test_physical_delete_is_not_allowed(self):
        self.assertEqual(self.api.delete(self.url).status_code, 405)
        self.assertTrue(Producto.objects.filter(pk=self.product.pk).exists())

    def test_categories_expose_stable_ids_and_status(self):
        public = APIClient().get(f'/api/categories/?sede={self.branch.pk}').data
        self.assertEqual(public, [{'id': self.category.pk, 'nombre': 'Comida', 'descripcion': 'Comidas de Centro', 'sede': self.branch.pk, 'activo': True}])
        self.assertEqual(len(self.api.get('/api/management/categories/').data), 2)

    def test_inactive_category_hides_its_products(self):
        self.category.activo = False; self.category.save()
        self.assertEqual(APIClient().get(f'/api/products/?sede={self.branch.pk}').data, [])
        self.assertEqual(len(APIClient().get(f'/api/products/?sede={self.other.pk}').data), 1)

    def test_filters_and_invalid_branch(self):
        public = APIClient()
        self.assertEqual(len(public.get(f'/api/products/?branch={self.branch.pk}&categoria=Comida&search=pizz').data), 1)
        self.assertEqual(public.get('/api/products/?search=ausente').data, [])
        self.assertEqual(public.get('/api/products/?sede=invalida').status_code, 400)

    def test_public_menu_ignores_expired_bearer(self):
        public = APIClient(); public.credentials(HTTP_AUTHORIZATION='Bearer expired')
        self.assertEqual(public.get('/api/products/').status_code, 200)

    def test_login_profile_and_inactive_user(self):
        public = APIClient()
        response = public.post('/api/auth/token/', {'username': 'operador', 'password': 'ClavePrueba-489!'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'operator')
        public.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        self.assertEqual(public.get('/api/me/').data['sede'], self.branch.pk)
        self.operator.is_active = False; self.operator.save()
        self.assertEqual(public.get('/api/me/').status_code, 401)

    def test_wrong_credentials(self):
        self.assertEqual(APIClient().post('/api/auth/token/', {'username': 'operador', 'password': 'bad'}, format='json').status_code, 401)

    def test_recovery_known_unknown_and_invalid_email(self):
        public = APIClient(); public.credentials(HTTP_AUTHORIZATION='Bearer expired')
        known = public.post('/api/auth/password-reset/', {'email': self.customer.email}, format='json')
        unknown = public.post('/api/auth/password-reset/', {'email': 'ausente@example.org'}, format='json')
        self.assertEqual(known.status_code, 200); self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(public.post('/api/auth/password-reset/', {'email': 'mal'}, format='json').status_code, 400)

    def test_recovery_link_changes_password_and_cannot_be_reused(self):
        public = APIClient()
        public.post('/api/auth/password-reset/', {'email': self.customer.email}, format='json')
        url = next(line for line in mail.outbox[-1].body.splitlines() if line.startswith('http'))
        self.assertEqual(urlsplit(url).path, '/restablecer-contrasena')
        params = parse_qs(urlsplit(url).query)
        data = {key: values[0] for key, values in params.items()}
        data['new_password'] = 'OtraClaveSegura-682!'
        self.assertEqual(public.post('/api/auth/password-reset/confirm/', data, format='json').status_code, 200)
        self.assertEqual(public.post('/api/auth/password-reset/confirm/', data, format='json').status_code, 400)
        self.customer.refresh_from_db(); self.assertTrue(self.customer.check_password(data['new_password']))

    def test_invalid_reset_link(self):
        self.assertEqual(APIClient().post('/api/auth/password-reset/confirm/', {'uid': 'bad', 'token': 'bad', 'new_password': 'ClaveFuerte-91!'}, format='json').status_code, 400)

    def test_order_rejects_deactivated_or_wrong_branch_product(self):
        self.api.force_authenticate(self.customer)
        for product in [self.other_product, self.product]:
            if product == self.product:
                product.activo = False; product.save()
            response = self.api.post('/api/orders/', {'sede': self.branch.pk, 'direccion_entrega': 'Casa', 'items': [{'producto_id': product.pk, 'cantidad': 1}]}, format='json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_order_accepts_published_product_and_keeps_price(self):
        self.api.force_authenticate(self.customer)
        response = self.api.post('/api/orders/', {'sede': self.branch.pk, 'direccion_entrega': 'Casa', 'items': [{'producto_id': self.product.pk, 'cantidad': 1}]}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Pedido.objects.get().detalles.get().precio_unitario_aplicado, self.product.precio_venta)

    def test_category_cannot_be_taken_from_another_branch(self):
        response = self.create(categoria=self.other_category.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn('categoria', response.data)
        response = self.api.patch(self.url, {'categoria': self.other_category.pk}, format='json')
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        self.assertEqual(self.product.categoria_id, self.category.pk)

    def test_operator_category_list_is_scoped(self):
        self.assertEqual(self.api.get(f'/api/management/categories/?sede={self.other.pk}').data, [])
        ids = [c['id'] for c in self.api.get('/api/management/categories/').data]
        self.assertNotIn(self.other_category.pk, ids)

    def test_category_name_is_unique_within_branch(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categoria.objects.create(nombre='Comida', sede=self.branch)
        self.assertEqual(Categoria.objects.filter(nombre='Comida').count(), 2)

    def test_login_contract_and_legacy_alias_for_every_role(self):
        courier = User.objects.create_user('reparto', password='ClavePrueba-489!', is_staff=True)
        PerfilPersonal.objects.create(usuario=courier, rol='courier', sede=self.branch)
        self.kitchen.set_password('ClavePrueba-489!'); self.kitchen.save()
        for user, role in [(self.customer, 'customer'), (self.operator, 'operator'),
                           (self.admin, 'admin'), (self.kitchen, 'kitchen'), (courier, 'courier')]:
            for path in ['/api/auth/login/', '/api/auth/login', '/api/auth/token/']:
                with self.subTest(role=role, path=path):
                    response = APIClient().post(path, {'username': user.username, 'password': 'ClavePrueba-489!'}, format='json')
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('access', response.data)
                    self.assertEqual(response.data['user']['role'], role)

    def test_login_errors_do_not_reveal_which_credential_failed(self):
        public = APIClient()
        wrong_user = public.post('/api/auth/login/', {'username': 'no-existe', 'password': 'ClavePrueba-489!'}, format='json')
        wrong_password = public.post('/api/auth/login/', {'username': 'operador', 'password': 'incorrecta'}, format='json')
        self.assertEqual(wrong_user.status_code, 401)
        self.assertEqual(wrong_user.data, wrong_password.data)

    def test_operator_cannot_deactivate_team_accounts(self):
        response = self.api.patch(f'/api/team-members/{self.kitchen.pk}/status/', {'is_active': False}, format='json')
        self.assertEqual(response.status_code, 403)
        self.kitchen.refresh_from_db()
        self.assertTrue(self.kitchen.is_active)

    def test_admin_can_change_staff_status_but_cannot_disable_itself(self):
        self.api.force_authenticate(self.admin)
        response = self.api.patch(f'/api/team-members/{self.operator.pk}/status/', {'is_active': False}, format='json')
        self.assertEqual(response.status_code, 200)
        self.operator.refresh_from_db()
        self.assertFalse(self.operator.is_active)
        response = self.api.patch(f'/api/team-members/{self.admin.pk}/status/', {'is_active': False}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_customer_list_is_reserved_for_operator_and_admin(self):
        for user, expected in [(self.operator, 200), (self.admin, 200), (self.kitchen, 403), (self.customer, 403)]:
            self.api.force_authenticate(user)
            self.assertEqual(self.api.get('/api/customers/').status_code, expected)

    @override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.BCryptSHA256PasswordHasher'])
    def test_login_with_project_bcrypt_hasher(self):
        self.customer.set_password('ClavePrueba-489!')
        self.customer.save()
        self.assertTrue(self.customer.password.startswith('bcrypt_sha256$'))
        response = APIClient().post('/api/auth/login/', {'username': self.customer.username, 'password': 'ClavePrueba-489!'}, format='json')
        self.assertEqual(response.status_code, 200)
