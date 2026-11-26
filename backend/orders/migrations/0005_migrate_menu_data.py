from django.db import migrations


def migrate_menu(apps, schema_editor):
    Product = apps.get_model('orders', 'Producto')
    Category = apps.get_model('orders', 'Categoria')
    Inventory = apps.get_model('orders', 'Inventario')
    for product in Product.objects.all().iterator():
        name = product.tipo_de_producto.strip()
        if name:
            category, _ = Category.objects.get_or_create(nombre=name)
            product.categoria_id = category.pk
        branches = list(Inventory.objects.filter(producto_id=product.pk).values_list('sede_id', flat=True).distinct())
        # No inventamos una sede para productos compartidos o sin inventario.
        if len(branches) == 1:
            product.sede_id = branches[0]
        product.save(update_fields=['categoria', 'sede'])


class Migration(migrations.Migration):
    dependencies = [('orders', '0004_menu_sprint1')]
    operations = [migrations.RunPython(migrate_menu, migrations.RunPython.noop)]
