import csv

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from areas.models import Area, SpatialResolution


class Command(BaseCommand):
    help = "Load UPRN areas from an Ordnance Survey CSV"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        with open(options["file"], "r") as f:
            reader = csv.reader(f)
            next(reader)
            batch = []
            batch_size = 1000
            uprn = None
            for row in reader:
                uprn = row[0]
                latitude = float(row[3])
                longitude = float(row[4])

                # TODO: This (using bulk create) is super slow, we'll probably need to use raw SQL
                area = Area(
                    name=uprn,
                    type=SpatialResolution.UPRN,
                    location=Point(longitude, latitude),
                )
                batch.append(area)

                if len(batch) >= batch_size:
                    self.save_batch(batch, uprn)
                    batch = []

            if len(batch) > 0:
                self.save_batch(batch, uprn)

    def save_batch(self, batch, last_uprn):
        Area.objects.bulk_create(batch)
        self.stdout.write(f"Imported up to {last_uprn}")
