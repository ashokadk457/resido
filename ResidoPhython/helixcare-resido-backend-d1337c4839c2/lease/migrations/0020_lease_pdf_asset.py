# Generated migration for adding pdf_asset field to Lease

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),  # Adjust based on your asset migrations
        (
            "lease",
            "0019_remove_moveinspectionlog_unique_move_inspection_per_datetime_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="lease",
            name="pdf_asset",
            field=models.ForeignKey(
                blank=True,
                help_text="Auto-generated lease PDF",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="lease_pdf",
                to="assets.asset",
            ),
        ),
    ]
