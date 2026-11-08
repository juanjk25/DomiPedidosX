from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import (
    Ciudad,
    Departamento,
    Inventario,
    Producto,
    Sede,
)


class Command(BaseCommand):
    help = "Crea datos de demostración compatibles con Database_Structure.sql."

    def handle(self, *args, **options):
        departamento, _ = Departamento.objects.get_or_create(
            nombre_departamento="Valle del Cauca"
        )
        ciudad, _ = Ciudad.objects.get_or_create(
            nombre_ciudad="Cali", departamento=departamento
        )
        sede, _ = Sede.objects.get_or_create(
            direccion="Carrera 1 # 10-20",
            defaults={
                "nombre_sede": "DomiPedidos Centro",
                "barrio_sede": "Centro",
                "ciudad": ciudad,
                "horario_atencion_apertura": "08:00",
                "horario_atencion_cierre": "22:00",
            },
        )
        seed = [
            ("770000000001", "Clásica de la casa", "Comida", "22000"),
            ("770000000002", "Doble queso", "Comida", "29000"),
            ("770000000003", "Limonada natural", "Bebida", "7000"),
            ("770000000004", "Gaseosa personal", "Bebida", "5000"),
        ]
        created = 0
        for barcode, name, product_type, price in seed:
            product, was_created = Producto.objects.get_or_create(
                codigo_de_barras=barcode,
                defaults={
                    "nombre_producto": name,
                    "tipo_de_producto": product_type,
                    "precio_compra": Decimal(price) * Decimal("0.6"),
                    "precio_venta": Decimal(price),
                },
            )
            Inventario.objects.get_or_create(
                producto=product,
                sede=sede,
                defaults={"cantidad_disponible": 30},
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Datos demo listos en '{sede.nombre_sede}'. "
                f"Productos nuevos: {created}."
            )
        )
