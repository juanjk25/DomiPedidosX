from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MenuMigrationTests(TransactionTestCase):
    def test_existing_products_and_unambiguous_branches_are_preserved(self):
        executor = MigrationExecutor(connection)
        old_target = [('orders', '0003_cliente_latitud_cliente_longitud')]
        new_target = [('orders', '0005_migrate_menu_data')]
        executor.migrate(old_target)
        try:
            old = executor.loader.project_state(old_target).apps
            dep = old.get_model('orders', 'Departamento').objects.create(nombre_departamento='Migración')
            city = old.get_model('orders', 'Ciudad').objects.create(nombre_ciudad='Ciudad migración', departamento=dep)
            Branch = old.get_model('orders', 'Sede')
            branches = [Branch.objects.create(nombre_sede=f'Sede {i}', barrio_sede='Centro', ciudad=city,
                direccion=f'Calle {i}', horario_atencion_apertura='08:00', horario_atencion_cierre='22:00') for i in (1, 2)]
            Product = old.get_model('orders', 'Producto')
            Inventory = old.get_model('orders', 'Inventario')
            products = [Product.objects.create(codigo_de_barras=str(i), nombre_producto=f'Producto {i}',
                tipo_de_producto='Comida', precio_compra=100, precio_venta=200) for i in (1, 2, 3)]
            Inventory.objects.create(producto=products[0], sede=branches[0])
            for branch in branches:
                Inventory.objects.create(producto=products[1], sede=branch)
            executor = MigrationExecutor(connection)
            executor.migrate(new_target)
            new = executor.loader.project_state(new_target).apps
            migrated = new.get_model('orders', 'Producto')
            first = migrated.objects.get(pk=products[0].pk)
            self.assertEqual(first.sede_id, branches[0].pk)
            self.assertEqual(first.categoria.nombre, 'Comida')
            self.assertEqual(first.precio_venta, 200)
            self.assertEqual(first.imagen_url, '')
            self.assertIsNone(migrated.objects.get(pk=products[1].pk).sede_id)
            self.assertIsNone(migrated.objects.get(pk=products[2].pk).sede_id)
            self.assertEqual(migrated.objects.count(), 3)
        finally:
            MigrationExecutor(connection).migrate([('orders', '0006_categorias_por_sede')])

    def test_global_categories_are_split_without_losing_products(self):
        previous = [('orders', '0005_migrate_menu_data')]
        latest = [('orders', '0006_categorias_por_sede')]
        executor = MigrationExecutor(connection)
        executor.migrate(previous)
        try:
            old = executor.loader.project_state(previous).apps
            dep = old.get_model('orders', 'Departamento').objects.create(nombre_departamento='Categorías')
            city = old.get_model('orders', 'Ciudad').objects.create(nombre_ciudad='Ciudad categorías', departamento=dep)
            branches = [old.get_model('orders', 'Sede').objects.create(nombre_sede=f'Sede {i}', barrio_sede='Centro', ciudad=city,
                direccion=f'Calle {i}', horario_atencion_apertura='08:00', horario_atencion_cierre='22:00') for i in (1, 2)]
            category = old.get_model('orders', 'Categoria').objects.create(nombre='Comida', activo=False)
            Product = old.get_model('orders', 'Producto')
            products = [Product.objects.create(codigo_de_barras=str(i), nombre_producto=f'Producto {i}',
                categoria=category, sede=branch, tipo_de_producto='Comida', precio_compra=100, precio_venta=200)
                for i, branch in enumerate(branches)]
            legacy = Product.objects.create(codigo_de_barras='legacy', nombre_producto='Compartido',
                categoria=category, tipo_de_producto='Comida', precio_compra=100, precio_venta=200)
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            new = executor.loader.project_state(latest).apps
            Product = new.get_model('orders', 'Producto')
            for product, branch in zip(products, branches):
                current = Product.objects.get(pk=product.pk)
                self.assertEqual(current.categoria.sede_id, branch.pk)
                self.assertFalse(current.categoria.activo)
                self.assertEqual(current.precio_venta, 200)
            self.assertNotEqual(Product.objects.get(pk=products[0].pk).categoria_id, Product.objects.get(pk=products[1].pk).categoria_id)
            self.assertIsNone(Product.objects.get(pk=legacy.pk).categoria.sede_id)
            self.assertEqual(Product.objects.count(), 3)
        finally:
            MigrationExecutor(connection).migrate(latest)
