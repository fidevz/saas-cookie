import apps.subscriptions.capabilities
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0002_alter_plan_stripe_price_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="capabilities",
            field=models.JSONField(
                blank=True,
                default=apps.subscriptions.capabilities.default_capabilities,
                help_text="Machine-readable feature gates for this plan.",
            ),
        ),
        migrations.AddField(
            model_name="subscription",
            name="capabilities",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Snapshot of the plan's capabilities at subscription time. Isolates existing subscribers from future plan changes.",
            ),
        ),
    ]
