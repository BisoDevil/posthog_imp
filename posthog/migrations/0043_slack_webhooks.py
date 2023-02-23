# Generated by Django 3.0.3 on 2020-04-06 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0042_add_type_dashboarditems"),
    ]

    operations = [
        migrations.AddField(model_name="action", name="post_to_slack", field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name="team",
            name="slack_incoming_webhook",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
