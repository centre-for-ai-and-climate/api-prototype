from areas.models import Area
from django.db import models


class EPC(models.Model):
    class Rating(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"
        F = "F", "F"
        G = "G", "G"

    timestamp = models.DateTimeField()
    current_energy_rating = models.CharField(max_length=1, choices=Rating.choices)
    potential_energy_rating = models.CharField(max_length=1, choices=Rating.choices)
    current_environmental_impact_tco2e = models.FloatField()
    potential_environmental_impact_tco2e = models.FloatField()
    floor_area_sqm = models.FloatField()
    yearly_primary_energy_use_kwh_sqm = models.FloatField()
    uprn = models.OneToOneField(Area, on_delete=models.CASCADE)
