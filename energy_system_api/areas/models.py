# Create your models here.
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _


class SpatialResolution(models.TextChoices):
    UK_REGION = "UK_REGION", _("UK Region")
    GRID_CONSTRAINT_ZONE = "GRID_CONSTRAINT_ZONE", _("Grid Constraint Zone")
    DNO = "DNO", _("DNO")
    LOCAL_AUTHORITY = "LOCAL_AUTHORITY", _("Local Authority")
    GRID_SUPPLY_POINT = "GRID_SUPPLY_POINT", _("Grid Supply Point")
    PRIMARY_SUBSTATION = "PRIMARY_SUBSTATION", _("Primary Substation")
    SECONDARY_SUBSTATION = "SECONDARY_SUBSTATION", _("Secondary Substation")
    LV_FEEDER = "LV_FEEDER", _("LV Feeder")
    POSTCODE_SECTOR = "POSTCODE_SECTOR", _("Postcode Sector")
    POSTCODE = "POSTCODE", _("Postcode")
    UPRN = "UPRN", _("UPRN")


class Area(gis_models.Model):
    name = models.TextField(db_index=True)
    type = models.CharField(
        max_length=50, choices=SpatialResolution.choices, db_index=True
    )
    geometry = gis_models.MultiPolygonField(null=True, blank=True)
    location = gis_models.PointField(null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.DO_NOTHING, null=True, blank=True
    )

    # TODO: Add versioning/Epochs/Generations
    # TODO: I don't think this is a good solution to resolving areas from source data
    # we probably need to look at a more robust solution like giving them URIs or
    # storing more identifiers, something else.
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "type", "location"],
                name="unique_secondary_substation_name_type_location",
                condition=models.Q(type=SpatialResolution.SECONDARY_SUBSTATION),
            ),
            models.UniqueConstraint(
                fields=["name", "type"],
                name="unique_lv_feeder_name_type",
                condition=models.Q(type=SpatialResolution.LV_FEEDER),
            ),
        ]

    def __str__(self):
        return f"{self.type} {self.name}"
