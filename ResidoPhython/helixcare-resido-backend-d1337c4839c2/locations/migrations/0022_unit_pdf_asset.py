# Generated migration for adding pdf_asset field to Unit

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0002_initial'),
        ('locations', '0021_customer_favicon_customer_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='pdf_asset',
            field=models.ForeignKey(blank=True, help_text='Auto-generated unit PDF', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unit_pdf', to='assets.asset'),
        ),
    ]

