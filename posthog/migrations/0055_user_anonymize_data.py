# Generated by Django 3.0.5 on 2020-05-21 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0054_dashboard_item_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="user", name="anonymize_data", field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]