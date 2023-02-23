import secrets
from typing import Optional

from django.contrib.postgres.fields.array import ArrayField
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_deprecate_fields import deprecate_field

from posthog.models.dashboard import Dashboard
from posthog.models.filters.utils import get_filter
from posthog.utils import generate_cache_key


def generate_short_id():
    return secrets.token_urlsafe(6)  # will result in 8-char strings (after encoding)


# TODO: Rename model to something more accurate like `Insight`
class DashboardItem(models.Model):
    """
    Stores saved insights along with their entire configuration options. Saved insights can be stored as standalone
    reports or part of a dashboard.
    """

    dashboard: models.ForeignKey = models.ForeignKey(
        "Dashboard", related_name="items", on_delete=models.CASCADE, null=True, blank=True
    )
    dive_dashboard: models.ForeignKey = models.ForeignKey("Dashboard", on_delete=models.SET_NULL, null=True, blank=True)
    name: models.CharField = models.CharField(max_length=400, null=True, blank=True)
    description: models.CharField = models.CharField(max_length=400, null=True, blank=True)
    team: models.ForeignKey = models.ForeignKey("Team", on_delete=models.CASCADE)
    filters: models.JSONField = models.JSONField(default=dict)
    filters_hash: models.CharField = models.CharField(max_length=400, null=True, blank=True)
    order: models.IntegerField = models.IntegerField(null=True, blank=True)
    deleted: models.BooleanField = models.BooleanField(default=False)
    saved: models.BooleanField = models.BooleanField(default=False)
    created_at: models.DateTimeField = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    layouts: models.JSONField = models.JSONField(default=dict)
    color: models.CharField = models.CharField(max_length=400, null=True, blank=True)
    last_refresh: models.DateTimeField = models.DateTimeField(blank=True, null=True)
    refreshing: models.BooleanField = models.BooleanField(default=False)
    created_by: models.ForeignKey = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    is_sample: models.BooleanField = models.BooleanField(
        default=False,
    )  # indicates if it's a sample graph generated by dashboard templates
    short_id: models.CharField = models.CharField(
        max_length=12, blank=True, default=generate_short_id,
    )  # Unique ID per team for easy sharing and short links
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    tags: ArrayField = ArrayField(models.CharField(max_length=32), blank=True, default=list)
    favorited: models.BooleanField = models.BooleanField(default=False)

    # ----- DEPRECATED ATTRIBUTES BELOW

    # Deprecated in favour of `display` within the Filter object
    type: models.CharField = deprecate_field(models.CharField(max_length=400, null=True, blank=True))

    # Deprecated as we don't store funnels as a separate model any more
    funnel: models.ForeignKey = deprecate_field(models.IntegerField(null=True, blank=True))

    class Meta:
        unique_together = (
            "team",
            "short_id",
        )

    def dashboard_filters(self, dashboard: Optional[Dashboard] = None):
        if dashboard is None:
            dashboard = self.dashboard
        if dashboard:
            return {**self.filters, **dashboard.filters}
        else:
            return self.filters


@receiver(pre_save, sender=Dashboard)
def dashboard_saved(sender, instance: Dashboard, **kwargs):
    for item in instance.items.all():
        dashboard_item_saved(sender, item, dashboard=instance, **kwargs)
        item.save()


@receiver(pre_save, sender=DashboardItem)
def dashboard_item_saved(sender, instance: DashboardItem, dashboard=None, **kwargs):
    if instance.filters and instance.filters != {}:
        filter = get_filter(data=instance.dashboard_filters(dashboard=dashboard), team=instance.team)

        instance.filters_hash = generate_cache_key("{}_{}".format(filter.toJSON(), instance.team_id))