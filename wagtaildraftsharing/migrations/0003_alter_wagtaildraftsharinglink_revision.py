# Generated by Django 5.1.1 on 2024-12-04 10:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wagtaildraftsharing", "0002_alter_wagtaildraftsharinglink_created_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wagtaildraftsharinglink",
            name="revision",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="wagtailcore.revision",
            ),
        ),
    ]
