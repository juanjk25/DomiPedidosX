from datetime import date, time

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import (
    Ciudad,
    Cliente,
    CredencialCliente,
    Departamento,
    HistorialEstadoPedido,
    Pedido,
    PerfilPersonal,
    PerfilTrabajador,
    Sede,
)
from orders.signals import pedido_estado_cambiado

User = get_user_model()


class OrderStatusTransitionTests(APITestCase):
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
            direccion="Calle 10 # 20-30",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )
        self.sede_sur = Sede.objects.create(
            nombre_sede="Sede Sur",
            barrio_sede="Ingeniero",
            ciudad=self.ciudad,
            direccion="Calle 5 # 80-10",
            horario_atencion_apertura=time(8, 0),
            horario_atencion_cierre=time(22, 0),
        )

        # Cliente y pedido base en Sede Norte
        self.customer_user = User.objects.create_user(
            username="cliente@test.com",
            email="cliente@test.com",
            password="Password123!",
        )
        self.cliente = Cliente.objects.create(
            tipo_documento="CC",
            numero_documento="1234567890",
            nombres="Ana",
            apellidos="Gomez",
            correo_cliente="cliente@test.com",
            fecha_nacimiento=date(1998, 5, 10),
        )
        CredencialCliente.objects.create(
            cliente=self.cliente,
            usuario=self.customer_user,
        )

        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            sede=self.sede_norte,
            estado_pedido=Pedido.Estado.PENDIENTE,
            direccion_entrega="Calle 15 # 40-20",
        )

        # Personal de Sede Norte (PerfilTrabajador)
        self.kitchen_user = self._create_worker(
            username="cocinero_norte",
            email="cocina.norte@test.com",
            rol=PerfilTrabajador.Rol.COCINA,
            sede=self.sede_norte,
        )
        self.courier_user = self._create_worker(
            username="repartidor_norte",
            email="repartidor.norte@test.com",
            rol=PerfilTrabajador.Rol.REPARTIDOR,
            sede=self.sede_norte,
        )
        self.operator_user = self._create_worker(
            username="operador_norte",
            email="operador.norte@test.com",
            rol=PerfilTrabajador.Rol.OPERADOR,
            sede=self.sede_norte,
        )
        self.admin_user = self._create_worker(
            username="admin_user",
            email="admin@test.com",
            rol=PerfilTrabajador.Rol.ADMINISTRADOR,
            sede=self.sede_norte,
            is_superuser=True,
        )

        # Cocinero de otra sede (Sede Sur)
        self.kitchen_other_branch = self._create_worker(
            username="cocinero_sur",
            email="cocina.sur@test.com",
            rol=PerfilTrabajador.Rol.COCINA,
            sede=self.sede_sur,
        )

        # Cocinero sin sede asignada
        self.kitchen_no_branch = self._create_worker(
            username="cocinero_sin_sede",
            email="cocina.sinsede@test.com",
            rol=PerfilTrabajador.Rol.COCINA,
            sede=None,
        )

    def _create_worker(self, username, email, rol, sede, is_superuser=False):
        user = User.objects.create_user(
            username=username,
            email=email,
            password="Password123!",
            is_staff=True,
            is_superuser=is_superuser,
        )
        PerfilTrabajador.objects.create(
            usuario=user,
            rol=rol,
            sede=sede,
        )
        return user

    def _url(self, pedido_id=None):
        pk = self.pedido.pk if pedido_id is None else pedido_id
        return reverse("order-status-update", kwargs={"pk": pk})

    def test_kitchen_transitions_pendiente_to_preparando_and_listo(self):
        self.client.force_authenticate(user=self.kitchen_user)

        # 1. Pendiente -> Preparando
        res_prep = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.PREPARANDO},
            format="json",
        )
        self.assertEqual(res_prep.status_code, status.HTTP_200_OK)
        self.assertEqual(res_prep.data["estado_anterior"], Pedido.Estado.PENDIENTE)
        self.assertEqual(res_prep.data["estado_actual"], Pedido.Estado.PREPARANDO)
        self.assertIn(Pedido.Estado.PENDIENTE, res_prep.data["timestamps_por_etapa"])
        self.assertIn(Pedido.Estado.PREPARANDO, res_prep.data["timestamps_por_etapa"])

        # 2. Preparando -> Listo
        res_listo = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.LISTO},
            format="json",
        )
        self.assertEqual(res_listo.status_code, status.HTTP_200_OK)
        self.assertEqual(res_listo.data["estado_anterior"], Pedido.Estado.PREPARANDO)
        self.assertEqual(res_listo.data["estado_actual"], Pedido.Estado.LISTO)
        self.assertEqual(len(res_listo.data["historial"]), 2)

        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_pedido, Pedido.Estado.LISTO)

        historial = list(
            HistorialEstadoPedido.objects.filter(pedido=self.pedido).order_by("id")
        )
        self.assertEqual(len(historial), 2)
        self.assertEqual(historial[0].rol_usuario, "kitchen")
        self.assertEqual(historial[0].usuario_id, self.kitchen_user.id)
        self.assertEqual(historial[1].estado_nuevo, Pedido.Estado.LISTO)
        self.assertLessEqual(historial[0].fecha_hora, historial[1].fecha_hora)

    def test_courier_transitions_listo_to_en_camino_and_entregado(self):
        self.pedido.estado_pedido = Pedido.Estado.LISTO
        self.pedido.save(update_fields=["estado_pedido"])

        self.client.force_authenticate(user=self.courier_user)

        # 1. Listo -> En camino
        res_camino = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.EN_CAMINO},
            format="json",
        )
        self.assertEqual(res_camino.status_code, status.HTTP_200_OK)
        self.assertEqual(res_camino.data["estado_anterior"], Pedido.Estado.LISTO)
        self.assertEqual(res_camino.data["estado_actual"], Pedido.Estado.EN_CAMINO)

        # 2. En camino -> Entregado
        res_entregado = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.ENTREGADO},
            format="json",
        )
        self.assertEqual(res_entregado.status_code, status.HTTP_200_OK)
        self.assertEqual(res_entregado.data["estado_anterior"], Pedido.Estado.EN_CAMINO)
        self.assertEqual(res_entregado.data["estado_actual"], Pedido.Estado.ENTREGADO)
        self.assertIn(Pedido.Estado.EN_CAMINO, res_entregado.data["timestamps_por_etapa"])
        self.assertIn(Pedido.Estado.ENTREGADO, res_entregado.data["timestamps_por_etapa"])

        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_pedido, Pedido.Estado.ENTREGADO)

        ultimo_historial = HistorialEstadoPedido.objects.filter(
            pedido=self.pedido
        ).last()
        self.assertIsNotNone(ultimo_historial)
        self.assertEqual(ultimo_historial.rol_usuario, "courier")
        self.assertEqual(ultimo_historial.usuario_id, self.courier_user.id)

    def test_signal_emitted_on_successful_transition_with_exact_timestamp(self):
        eventos = []

        def receiver(sender, **kwargs):
            eventos.append({"sender": sender, **kwargs})

        pedido_estado_cambiado.connect(receiver)
        try:
            self.client.force_authenticate(user=self.kitchen_user)
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.patch(
                    self._url(),
                    {"estado": Pedido.Estado.PREPARANDO},
                    format="json",
                )
        finally:
            pedido_estado_cambiado.disconnect(receiver)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(eventos), 1)

        evento = eventos[0]
        historial = HistorialEstadoPedido.objects.get(pedido=self.pedido)
        self.assertEqual(evento["sender"], Pedido)
        self.assertEqual(evento["pedido"].pk, self.pedido.pk)
        self.assertEqual(evento["estado_anterior"], Pedido.Estado.PENDIENTE)
        self.assertEqual(evento["estado_nuevo"], Pedido.Estado.PREPARANDO)
        self.assertEqual(evento["usuario"].pk, self.kitchen_user.pk)
        self.assertEqual(evento["rol_usuario"], "kitchen")
        self.assertEqual(evento["historial"].pk, historial.pk)
        self.assertEqual(evento["timestamp"], historial.fecha_hora)

    def test_invalid_transitions_rejected_without_history_or_signal(self):
        eventos = []

        def receiver(sender, **kwargs):
            eventos.append(kwargs)

        pedido_estado_cambiado.connect(receiver)
        try:
            self.client.force_authenticate(user=self.kitchen_user)
            with self.captureOnCommitCallbacks(execute=True):
                # Salto inválido: Pendiente -> Listo
                res_salto = self.client.patch(
                    self._url(),
                    {"estado": Pedido.Estado.LISTO},
                    format="json",
                )
                # Estado inexistente
                res_invalido = self.client.patch(
                    self._url(),
                    {"estado": "Desconocido"},
                    format="json",
                )
                # Retroceso inválido: Preparando -> Pendiente
                self.pedido.estado_pedido = Pedido.Estado.PREPARANDO
                self.pedido.save(update_fields=["estado_pedido"])
                res_retroceso = self.client.patch(
                    self._url(),
                    {"estado": Pedido.Estado.PENDIENTE},
                    format="json",
                )
                # Estado terminal: Cancelado -> Preparando
                self.pedido.estado_pedido = Pedido.Estado.CANCELADO
                self.pedido.save(update_fields=["estado_pedido"])
                res_cancelado = self.client.patch(
                    self._url(),
                    {"estado": Pedido.Estado.PREPARANDO},
                    format="json",
                )
        finally:
            pedido_estado_cambiado.disconnect(receiver)

        self.assertEqual(res_salto.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_invalido.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_retroceso.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_cancelado.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(HistorialEstadoPedido.objects.count(), 0)
        self.assertEqual(len(eventos), 0)

    def test_role_cross_transitions_are_forbidden(self):
        # Repartidor no puede pasar Pendiente -> Preparando
        self.client.force_authenticate(user=self.courier_user)
        res_courier = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.PREPARANDO},
            format="json",
        )
        self.assertEqual(res_courier.status_code, status.HTTP_403_FORBIDDEN)

        # Cocinero no puede pasar Listo -> En camino
        self.pedido.estado_pedido = Pedido.Estado.LISTO
        self.pedido.save(update_fields=["estado_pedido"])
        self.client.force_authenticate(user=self.kitchen_user)
        res_kitchen = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.EN_CAMINO},
            format="json",
        )
        self.assertEqual(res_kitchen.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_roles_and_anonymous_are_rejected(self):
        # Sin autenticación -> 401
        res_anon = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.PREPARANDO},
            format="json",
        )
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # Cliente, Operador y Admin -> 403
        for user in (self.customer_user, self.operator_user, self.admin_user):
            self.client.force_authenticate(user=user)
            res = self.client.patch(
                self._url(),
                {"estado": Pedido.Estado.PREPARANDO},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_cannot_update_order_from_another_branch(self):
        self.client.force_authenticate(user=self.kitchen_other_branch)
        response = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.PREPARANDO},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_without_branch_is_forbidden(self):
        self.client.force_authenticate(user=self.kitchen_no_branch)
        response = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.PREPARANDO},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_order_returns_404(self):
        self.client.force_authenticate(user=self.kitchen_user)
        response = self.client.patch(
            self._url(pedido_id=999999),
            {"estado": Pedido.Estado.PREPARANDO},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_kitchen_with_perfil_personal_is_supported(self):
        personal_kitchen = User.objects.create_user(
            username="cocina_personal",
            email="cocina.personal@test.com",
            password="Password123!",
            is_staff=True,
        )
        PerfilPersonal.objects.create(
            usuario=personal_kitchen,
            rol="kitchen",
            sede=self.sede_norte,
        )

        self.client.force_authenticate(user=personal_kitchen)
        response = self.client.patch(
            self._url(),
            {"estado": Pedido.Estado.PREPARANDO},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado_actual"], Pedido.Estado.PREPARANDO)