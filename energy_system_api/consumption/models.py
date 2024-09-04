from areas.models import Area, SpatialResolution
from django.db import models
from django.utils.translation import gettext_lazy as _


class Consumption(models.Model):
    class TemporalResolution(models.TextChoices):
        HALF_HOUR = "30M", _("Half Hourly")
        HOUR = "1H", _("Hourly")
        DAY = "1D", _("Daily")

    kwh = models.FloatField()
    spatial_resolution = models.CharField(
        max_length=50, choices=SpatialResolution.choices, db_index=True
    )
    temporal_resolution = models.CharField(
        max_length=3, choices=TemporalResolution.choices, db_index=True
    )
    start_timestamp = models.DateTimeField(db_index=True)
    end_timestamp = models.DateTimeField(db_index=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    number_of_meters = models.IntegerField()

    class Meta:
        verbose_name_plural = "consumption"
