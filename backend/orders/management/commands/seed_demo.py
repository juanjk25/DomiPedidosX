from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Branch, Category, Product

class Command(BaseCommand):
    help = "Crea una sede, categorías y productos ficticios para la demo local."
    def handle(self, *args, **options):
        branch, _ = Branch.objects.get_or_create(name="DomiPedidos Centro", defaults={"address": "Carrera 1 # 10-20, Cali", "phone": "6025550101", "delivery_fee": Decimal("5000")})
        seed = {"Hamburguesas": [("Clásica de la casa", "Carne, queso, lechuga y salsa de la casa.", "22000", 25), ("Doble queso", "Doble carne y queso cheddar.", "29000", 30)], "Bebidas": [("Limonada natural", "Limonada preparada al momento.", "7000", 5), ("Gaseosa personal", "Botella personal fría.", "5000", 2)]}
        created = 0
        for category_name, products in seed.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, description, price, minutes in products:
                _, was_created = Product.objects.get_or_create(branch=branch, name=name, defaults={"category": category, "description": description, "price": Decimal(price), "preparation_minutes": minutes, "stock": 30})
                created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Datos demo listos en '{branch.name}'. Productos nuevos: {created}."))
