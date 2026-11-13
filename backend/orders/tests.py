from datetime import time
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Departamento, Ciudad, Sede, PerfilTrabajador

User = get_user_model()


class AsignarRolTrabajadorTests(APITestCase):
    """
    Pruebas unitarias para HU-A9: Asignar rol a integrante del equipo.
    Cumple con el Definition of Done (DoD):
    1. El endpoint permite al administrador crear una cuenta de trabajador con rol asignado.
    2. El trabajador queda activo en el sistema (is_active=True).
    3. No se permite crear con un correo ya existente.
    4. La vista permite asignar y persistir el rol y sede.
    5. Un usuario no administrador no tiene permisos para crear trabajadores.
    """

    def setUp(self):
        # 1. Crear sede base para asignación
        self.depto = Departamento.objects.create(nombre_departamento="Valle del Cauca")
        self.ciudad = Ciudad.objects.create(
            nombre_ciudad="Cali", departamento=self.depto
        )
        self.sede = Sede.objects.create(
            nombre_sede="Sede Norte",
            barrio_sede="Granada",
            ciudad=self.ciudad,
            direccion="Av 9 # 12-34",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )

        # 2. Administrador que realiza la gestión laboral
        self.admin = User.objects.create_superuser(
            username="admin_test",
            email="admin@domipedidos.com",
            password="AdminPassword123!",
        )

        # 3. Usuario regular sin permisos
        self.cliente = User.objects.create_user(
            username="cliente_comun",
            email="cliente@correo.com",
            password="ClientePass123!",
        )

        self.url = "/api/team-members/"

    def test_admin_crea_trabajador_con_rol_exitosamente(self):
        """Un administrador puede crear una cuenta de trabajador con su rol y sede."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            "username": "carlos_cocina",
            "email": "carlos@domipedidos.com",
            "first_name": "Carlos",
            "last_name": "Perez",
            "password": "PasswordSegura123!",
            "rol": "cocina",
            "sede_id": self.sede.id_sede,
            "telefono": "3159876543",
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "carlos_cocina")
        self.assertEqual(response.data["email"], "carlos@domipedidos.com")
        self.assertEqual(response.data["rol"], "cocina")
        self.assertTrue(response.data["is_active"])

        # Verificar persistencia en base de datos
        nuevo_usuario = User.objects.get(username="carlos_cocina")
        self.assertTrue(nuevo_usuario.is_active)
        self.assertTrue(nuevo_usuario.is_staff)
        self.assertTrue(nuevo_usuario.check_password("PasswordSegura123!"))

        perfil = PerfilTrabajador.objects.get(usuario=nuevo_usuario)
        self.assertEqual(perfil.rol, "cocina")
        self.assertEqual(perfil.sede, self.sede)
        self.assertEqual(perfil.telefono, "3159876543")

    def test_rechaza_correo_duplicado(self):
        """El sistema no permite registrar un trabajador con un correo que ya existe."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            "username": "otro_usuario",
            "email": self.admin.email,  # Mismo correo que el admin
            "first_name": "Juan",
            "last_name": "Lopez",
            "password": "Password123!",
            "rol": "repartidor",
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_rechaza_rol_no_valido(self):
        """El sistema solo permite roles definidos en la matriz de roles."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            "username": "usuario_invalido",
            "email": "invalido@domipedidos.com",
            "first_name": "Pedro",
            "last_name": "Picapiedra",
            "password": "Password123!",
            "rol": "rol_inexistente",
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rol", response.data)

    def test_usuario_no_admin_recibe_prohibido(self):
        """Un usuario que no sea administrador no puede crear integrantes del equipo."""
        self.client.force_authenticate(user=self.cliente)
        payload = {
            "username": "hacker",
            "email": "hacker@test.com",
            "first_name": "Hacker",
            "last_name": "Anon",
            "password": "Password123!",
            "rol": "administrador",
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_puede_listar_equipo_de_trabajo(self):
        """El administrador puede consultar el listado de todo el personal activo."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
