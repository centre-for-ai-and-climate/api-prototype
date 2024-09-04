import csv
import datetime

from areas.models import Area, SpatialResolution
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.core.management.base import BaseCommand

from consumption.models import Consumption


class Command(BaseCommand):
    help = "Load Energy Consumption and Areas from DNO CSVs"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument("dno", type=str)

    def handle(self, *args, **options):
        with open(options["file"], "r") as f:
            reader = csv.DictReader(f)
            batch = []
            batch_size = 10000
            row_number = 0
            for row in reader:
                row_number += 1
                if (
                    row["total_consumption_active_import"] == ""
                    or row["aggregated_device_count_active"] == ""
                ):
                    self.stderr.write(f"Skipping row {row_number} due to missing data")
                    continue
                substation = self.get_or_create_substation(options, row)
                feeder = self.get_or_create_lv_feeder(row, substation)
                end_timestamp, start_timestamp = self.calculate_timestamps(row)
                consumption = Consumption(
                    kwh=float(row["total_consumption_active_import"]),
                    spatial_resolution=SpatialResolution.LV_FEEDER,
                    temporal_resolution=Consumption.TemporalResolution.HALF_HOUR,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    area=feeder,
                    number_of_meters=float(row["aggregated_device_count_active"]),
                )
                batch.append(consumption)

                if len(batch) >= batch_size:
                    self.save_batch(batch, row_number)
                    batch = []

            if len(batch) > 0:
                self.save_batch(batch, row_number)

    def calculate_timestamps(self, row):
        # Calculate the start time from the end time given
        # TODO: check timestamps given are the end of the 30 minute period
        end_timestamp = datetime.datetime.fromisoformat(
            row["data_collection_log_timestamp"]
        )
        start_timestamp = end_timestamp - datetime.timedelta(minutes=30)
        return end_timestamp, start_timestamp

    def get_or_create_lv_feeder(self, row, substation):
        feeder_name = f"{substation.name} Feeder {row["lv_feeder_id"]} {row["lv_feeder_name"]}".strip()
        feeder = cache.get(feeder_name)
        if feeder is None:
            feeder, created = Area.objects.get_or_create(
                name=feeder_name,
                type=SpatialResolution.LV_FEEDER,
                parent=substation,
            )
            cache.set(feeder_name, feeder)
        return feeder

    def get_or_create_substation(self, options, row):
        # Using a rudimentary caching approach here since the areas tend to be in
        # order and there aren't many of them when compared to the number of
        # rows, so we can save a lot of queries.
        # TODO: This probably needs lots more thought though.
        substation_name = f"{options["dno"]} Substation {row["secondary_substation_id"]} {row["secondary_substation_name"]}"
        substation = cache.get(substation_name)
        if substation is None:
            substation_location = self.parse_substation_location(row)
            substation, created = Area.objects.get_or_create(
                name=substation_name,
                type=SpatialResolution.SECONDARY_SUBSTATION,
                location=substation_location,
            )
            cache.set(substation_name, substation)
        return substation

    def parse_substation_location(self, row):
        raw_location = row["substation_geo_location"]
        if not raw_location or raw_location == "":
            return None
        (lat, lng) = raw_location.split(",")
        (lat, lng) = lat.strip(), lng.strip()
        (lat, lng) = float(lat), float(lng)
        # Rounding to 5 DP gets us an accuracy of +/- 1.1m
        return Point(round(lat, 5), round(lng, 5))

    def save_batch(self, batch, row_number):
        Consumption.objects.bulk_create(batch)
        self.stdout.write(f"Imported up to {row_number}")
