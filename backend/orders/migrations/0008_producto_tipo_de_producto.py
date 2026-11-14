from django.db import migrations, models


def add_product_type(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(cursor, "productos")
        }
    if "tipo_de_producto" not in columns:
        schema_editor.execute(
            "ALTER TABLE productos ADD COLUMN tipo_de_producto VARCHAR(50) NOT NULL DEFAULT ''"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0007_merge_0004_perfiltrabajador_0006_categorias_por_sede"),
    ]

    operations = [
        migrations.RunPython(add_product_type, migrations.RunPython.noop),
    ]
