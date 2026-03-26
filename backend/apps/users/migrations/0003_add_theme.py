from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_add_pending_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="theme",
            field=models.CharField(
                choices=[("system", "System"), ("light", "Light"), ("dark", "Dark")],
                default="system",
                max_length=10,
            ),
        ),
    ]
