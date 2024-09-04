import csv
from collections import defaultdict

from django.contrib.gis.db.models import Union
from django.contrib.gis.geos import MultiPolygon
from django.core.management.base import BaseCommand
from django.db.models import Count

from areas.models import Area, SpatialResolution


class Command(BaseCommand):
    help = "Augment LV Feeder areas with postcode geometries"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument("dno", type=str)

    def handle(self, *args, **options):
        # The file lists each postcode and the LV feeder which supplies it. In order to
        # augment the LV feeder areas with the postcode geometries, we need to get all
        # the postcodes for each LV feeder and then combine their geometries.
        # Therefore we do two loops, once over the file to get the postcodes for each
        # LV feeder, and then a second loop to combine the geometries for each feeder.
        postcodes_per_feeder = defaultdict(list)
        with open(options["file"], "r") as f:
            reader = csv.DictReader(f)
            row_number = 0

            for row in reader:
                row_number += 1
                if row["postcode"] == "":
                    self.stderr.write(f"Skipping row {row_number} due to missing data")
                    continue
                feeder_id = f"{options["dno"]} Substation {row["secondary_substation_id"]} {row["secondary_substation_name"]} Feeder {row["lv_feeder_id"]} {row["lv_feeder_name"]}".strip()
                postcodes_per_feeder[feeder_id].append(row["postcode"])

            self.stdout.write(
                f"Found {len(postcodes_per_feeder)} LV feeders with postcodes"
            )

            batch = []
            batch_size = 1000
            row_number = 0
            missing_areas = 0
            areas_missing_postcodes = 0
            areas_with_no_postcodes = 0
            for feeder_id, postcodes in postcodes_per_feeder.items():
                row_number += 1
                try:
                    feeder = Area.objects.get(
                        name=feeder_id, type=SpatialResolution.LV_FEEDER
                    )
                except Area.DoesNotExist:
                    missing_areas += 1
                    self.stderr.write(
                        f"Skipping {feeder_id} as does not exist in our DB"
                    )
                    continue

                combined = Area.objects.filter(
                    name__in=postcodes, type=SpatialResolution.POSTCODE
                ).aggregate(Union("geometry"), Count("name"))

                if combined["name__count"] == 0:
                    areas_with_no_postcodes += 1
                    self.stderr.write(
                        f"Skipping {feeder_id} as no postcode geometries found to combine"
                    )
                    continue

                if combined["name__count"] != len(postcodes):
                    areas_missing_postcodes += 1
                    self.stderr.write(
                        f"Warning, found {combined["name__count"]} postcodes in our DB for {feeder_id} but expected {len(postcodes)}"
                    )

                feeder.geometry = self.fix_multipolygon(combined["geometry__union"])

                batch.append(feeder)

                if len(batch) >= batch_size:
                    self.save_batch(batch, row_number)
                    batch = []

            if len(batch) > 0:
                self.save_batch(batch, row_number)

            self.stdout.write(f"Missing areas: {missing_areas}")
            self.stdout.write(
                f"Areas missing some postcodes: {areas_missing_postcodes}"
            )
            self.stdout.write(
                f"Areas with no postcodes at all: {areas_with_no_postcodes}"
            )

    def fix_multipolygon(self, geom):
        if isinstance(geom, MultiPolygon):
            return geom
        else:
            return MultiPolygon([geom])

    def save_batch(self, batch, row_number):
        Area.objects.bulk_update(batch, ["geometry"])
        self.stdout.write(f"Processed up to {row_number}")
