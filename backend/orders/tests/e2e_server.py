"""Servidor efímero para Playwright. Usa exclusivamente SQLite de pruebas."""
import json
import os
from pathlib import Path
import sys
import tempfile

backend = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.test_settings'
with tempfile.TemporaryDirectory(prefix='domi-e2e-') as temp:
    os.environ['DOMI_TEST_DB'] = str(Path(temp) / 'test.sqlite3')
    import django
    django.setup()
    from django.core.management import call_command
    from django.contrib.auth import get_user_model
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode
    from orders.models import Categoria, Cliente, CredencialCliente, PerfilPersonal, Producto, Sede
    call_command('migrate', verbosity=0)
    call_command('seed_demo', verbosity=0)
    User = get_user_model()
    branch = Sede.objects.first()
    operator = User.objects.create_user('operador', 'operador@example.org', 'ClavePrueba-489!', is_staff=True)
    PerfilPersonal.objects.create(usuario=operator, rol='operator', sede=branch)
    for index, email in enumerate(['cliente@example.org', 'reset@example.org']):
        user = User.objects.create_user(email, email, 'ClavePrueba-489!')
        profile = Cliente.objects.create(tipo_documento='CC', numero_documento=f'e2e-{index}', nombres='Cliente', apellidos='Prueba', correo_cliente=email, fecha_nacimiento='2000-01-01', direccion_residencia='Calle de prueba 12')
        CredencialCliente.objects.create(cliente=profile, usuario=user)
        if email == 'reset@example.org':
            data_dir = backend.parent / 'frontend' / '.e2e-data'
            data_dir.mkdir(exist_ok=True)
            (data_dir / 'reset-link.json').write_text(json.dumps({'uid': urlsafe_base64_encode(force_bytes(user.pk)), 'token': default_token_generator.make_token(user)}))
    call_command('runserver', '127.0.0.1:8000', use_reloader=False)
