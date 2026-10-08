import django.conf
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("orders", "0001_initial")]
    operations = [migrations.CreateModel(name="CustomerAddress", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("label", models.CharField(default="Casa", max_length=60)), ("address", models.CharField(max_length=300)), ("reference", models.CharField(blank=True, max_length=200)), ("is_default", models.BooleanField(default=False)), ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_addresses", to=django.conf.settings.AUTH_USER_MODEL))], options={"ordering": ["-is_default", "label", "id"]})]
