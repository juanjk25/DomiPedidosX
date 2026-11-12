from datetime import time
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Departamento, Ciudad, Sede

User = get_user_model()


class SedeHorarioTests(APITestCase):
    """
    Pruebas unitarias para HU-E8: Configuración del horario de atención de la sede.
    Verifica que:
    1. Cualquier cliente pueda consultar el horario (GET).
    2. Un operador/administrador pueda modificar el horario (PATCH/PUT).
    3. Se rechace una hora de cierre anterior o igual a la de apertura (Validación).
    4. Un usuario anónimo o no autorizado no pueda modificar el horario (Seguridad).
    """

    def setUp(self):
        # 1. Crear ubicación geográfica base
        self.depto = Departamento.objects.create(nombre_departamento="Valle del Cauca")
        self.ciudad = Ciudad.objects.create(
            nombre_ciudad="Cali", departamento=self.depto
        )

        # 2. Crear una sede de prueba
        self.sede = Sede.objects.create(
            nombre_sede="Sede San Antonio",
            barrio_sede="San Antonio",
            ciudad=self.ciudad,
            direccion="Calle 5 # 10-20",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )

        # 3. URL del endpoint
        self.url = f"/api/branches/{self.sede.id_sede}/horario/"

        # 4. Crear usuario operador/admin (staff)
        self.operador = User.objects.create_user(
            username="operador_test",
            email="operador@test.com",
            password="TestPassword123!",
            is_staff=True,
        )

        # 5. Crear usuario cliente normal
        self.cliente = User.objects.create_user(
            username="cliente_test",
            email="cliente@test.com",
            password="TestPassword123!",
        )

    def test_consultar_horario_publico(self):
        """Cualquier usuario puede consultar el horario sin estar autenticado."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre_sede"], "Sede San Antonio")
        self.assertEqual(response.data["horario_atencion_apertura"], "08:00:00")
        self.assertEqual(response.data["horario_atencion_cierre"], "22:00:00")
        self.assertIn("esta_abierta", response.data)

    def test_operador_puede_actualizar_horario(self):
        """Un operador autorizado puede actualizar el horario con éxito."""
        self.client.force_authenticate(user=self.operador)
        data = {"horario_atencion_cierre": "23:30:00"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.sede.refresh_from_db()
        self.assertEqual(self.sede.horario_atencion_cierre, time(23, 30))

    def test_rechaza_hora_cierre_anterior_a_apertura(self):
        """Valida que no se permitan horas ilógicas (cierre antes que apertura)."""
        self.client.force_authenticate(user=self.operador)
        data = {"horario_atencion_cierre": "07:00:00"}  # Abre a las 08:00:00
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("horario_atencion_cierre", response.data)

    def test_usuario_anonimo_no_puede_modificar(self):
        """Un usuario sin autenticar recibe 401 Unauthorized al intentar modificar."""
        data = {"horario_atencion_cierre": "23:00:00"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
