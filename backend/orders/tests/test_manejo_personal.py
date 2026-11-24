from datetime import time

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import (
    AuditoriaPersonal,
    Ciudad,
    Departamento,
    PerfilTrabajador,
    Sede,
)

User = get_user_model()


class ManejoPersonalAdminTests(APITestCase):
    """
    Pruebas unitarias para HU-A11: Manejo de personal a nivel de administrador.
    """

    def setUp(self):
        self.depto = Departamento.objects.create(nombre_departamento="Valle del Cauca")
        self.ciudad = Ciudad.objects.create(
            nombre_ciudad="Cali", departamento=self.depto
        )
        self.sede = Sede.objects.create(
            nombre_sede="Sede Norte",
            barrio_sede="Granada",
            ciudad=self.ciudad,
            direccion="Av 6N # 20-10",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )

        self.admin = User.objects.create_superuser(
            username="admin_principal",
            email="admin_principal@domipedidos.com",
            password="AdminPassword123!",
        )

        self.cocinero = User.objects.create_user(
            username="chef_sede",
            email="chef@domipedidos.com",
            password="ChefPassword123!",
            is_staff=True,
            is_active=True,
        )
        PerfilTrabajador.objects.create(
            usuario=self.cocinero,
            rol=PerfilTrabajador.Rol.COCINA,
            sede=self.sede,
            telefono="3001234567",
        )

        self.cliente = User.objects.create_user(
            username="cliente_normal",
            email="cliente_normal@correo.com",
            password="ClientePassword123!",
        )

        self.list_url = "/api/team-members/"
        self.audit_url = "/api/team-members/audit/"

    def test_admin_desactiva_y_reactiva_cuenta_con_auditoria(self):
        self.client.force_authenticate(user=self.admin)
        status_url = f"/api/team-members/{self.cocinero.id}/status/"

        # Desactivar
        resp_off = self.client.patch(
            status_url,
            {"is_active": False, "motivo": "Vacaciones"},
            format="json",
        )
        self.assertEqual(resp_off.status_code, status.HTTP_200_OK)
        self.assertFalse(resp_off.data["is_active"])
        self.cocinero.refresh_from_db()
        self.assertFalse(self.cocinero.is_active)

        # Reactivar
        resp_on = self.client.patch(
            status_url,
            {"is_active": True, "motivo": "Reingreso"},
            format="json",
        )
        self.assertEqual(resp_on.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_on.data["is_active"])
        self.cocinero.refresh_from_db()
        self.assertTrue(self.cocinero.is_active)

        # Verificar auditoría en BD y endpoint
        auditorias = AuditoriaPersonal.objects.filter(usuario_afectado=self.cocinero)
        self.assertEqual(auditorias.count(), 2)
        self.assertEqual(auditorias.first().estado_nuevo, True)
        self.assertEqual(auditorias.first().motivo, "Reingreso")

        resp_audit = self.client.get(self.audit_url)
        self.assertEqual(resp_audit.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_audit.data), 2)

    def test_admin_no_puede_desactivar_su_propia_cuenta(self):
        self.client.force_authenticate(user=self.admin)
        status_url = f"/api/team-members/{self.admin.id}/status/"

        response = self.client.patch(
            status_url, {"is_active": False}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(AuditoriaPersonal.objects.count(), 0)

    def test_personal_no_admin_no_puede_listar_ni_cambiar_estado(self):
        self.client.force_authenticate(user=self.cocinero)
        status_url = f"/api/team-members/{self.admin.id}/status/"

        self.assertEqual(
            self.client.get(self.list_url).status_code, status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            self.client.patch(status_url, {"is_active": False}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_cliente_no_puede_cambiar_estado(self):
        self.client.force_authenticate(user=self.cliente)
        status_url = f"/api/team-members/{self.cocinero.id}/status/"

        response = self.client.patch(
            status_url, {"is_active": False}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        