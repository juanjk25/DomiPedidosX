from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cliente, CredencialCliente

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        # Nota: Como el modelo 'Cliente' exige campos obligatorios (fecha_nacimiento, etc.), 
        # debes proporcionar valores por defecto o manejar la creación directamente en las vistas/serializers 
        # en lugar de usar signals. Aquí un ejemplo temporal:
        cliente, cliente_created = Cliente.objects.get_or_create(
            correo_cliente=instance.email,
            defaults={
                'tipo_documento': 'CC',
                'numero_documento': f'TEMP-{instance.id}',
                'nombres': instance.first_name or instance.username,
                'apellidos': instance.last_name or 'Sin apellido',
                'fecha_nacimiento': '2000-01-01'
            }
        )
        CredencialCliente.objects.get_or_create(usuario=instance, cliente=cliente)