# Generated by Django 5.1 on 2024-08-28 15:54

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Area",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.TextField()),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("UK_REGION", "UK Region"),
                            ("GRID_CONSTRAINT_ZONE", "Grid Constraint Zone"),
                            ("LOCAL_AUTHORITY", "Local Authority"),
                            ("GRID_SUPPLY_POINT", "Grid Supply Point"),
                            ("PRIMARY_SUBSTATION", "Primary Substation"),
                            ("SECONDARY_SUBSTATION", "Secondary Substation"),
                            ("LV_FEEDER", "LV Feeder"),
                            ("POSTCODE_SECTOR", "Postcode Sector"),
                            ("UPRN", "UPRN"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="areas.area",
                    ),
                ),
            ],
        ),
    ]
