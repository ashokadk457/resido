# Generated migration - Add device_fingerprint field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("residents", "0011_residenteviction_reject_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="residentregistereddevice",
            name="device_fingerprint",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
