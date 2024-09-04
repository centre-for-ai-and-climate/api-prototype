import csv
import datetime
import os

import pytz
from areas.models import Area, SpatialResolution
from django.core.management.base import BaseCommand
from django.db.utils import DataError

from building_performance.models import EPC


class Command(BaseCommand):
    help = "Load Energy Consumption and Areas from DNO CSVs"

    def add_arguments(self, parser):
        parser.add_argument("directory", type=str)

    def handle(self, *args, **options):
        # Assume, given lack of info, that EPCs are in UK time (i.e. BST or GMT
        # depending on the time of year) not UTC.
        tz = pytz.timezone("Europe/London")
        row_number = 0
        them_missing_uprns = 0
        us_missing_uprns = 0
        for root, dirs, filenames in os.walk(options["directory"]):
            dirs.sort()
            filenames.sort()
            for filename in filenames:
                if filename != "certificates.csv":
                    continue
                full_filename = os.path.join(root, filename)
                with open(full_filename, "r") as f:
                    self.stdout.write(f"Importing {full_filename}")
                    reader = csv.DictReader(f)
                    for row in reader:
                        row_number += 1
                        if row_number <= 1754782:
                            continue
                        if row["UPRN"] == "":
                            them_missing_uprns += 1
                            continue
                        if self.invalid_row(
                            row,
                            [
                                "UPRN",
                                "LODGEMENT_DATETIME",
                                "CURRENT_ENERGY_RATING",
                                "POTENTIAL_ENERGY_RATING",
                                "ENVIRONMENT_IMPACT_CURRENT",
                                "ENVIRONMENT_IMPACT_POTENTIAL",
                                "TOTAL_FLOOR_AREA",
                                "ENERGY_CONSUMPTION_CURRENT",
                            ],
                        ):
                            self.stderr.write(
                                f"Skipping row {row_number} due to missing data"
                            )
                            continue
                        try:
                            uprn = Area.objects.get(
                                name=row["UPRN"], type=SpatialResolution.UPRN
                            )
                        except Area.DoesNotExist:
                            us_missing_uprns += 1
                            self.stderr.write(
                                f"Skipping row {row_number} due to missing UPRN: {row["UPRN"]}"
                            )
                            continue
                        except Area.MultipleObjectsReturned:
                            self.stderr.write(
                                f"Skipping row {row_number} due to multiple matching UPRNs: {row["UPRN"]}"
                            )
                            continue

                        # Can't do an easy bulk insert here because we want to override
                        # existing data if it's changed.
                        # TODO: Might be a good reason to not do that and instead keep
                        # a history of EPCs.
                        try:
                            EPC.objects.update_or_create(
                                uprn=uprn,
                                defaults={
                                    "timestamp": tz.localize(
                                        datetime.datetime.fromisoformat(
                                            row["LODGEMENT_DATETIME"]
                                        )
                                    ),
                                    "current_energy_rating": row[
                                        "CURRENT_ENERGY_RATING"
                                    ],
                                    "potential_energy_rating": row[
                                        "POTENTIAL_ENERGY_RATING"
                                    ],
                                    "current_environmental_impact_tco2e": float(
                                        row["ENVIRONMENT_IMPACT_CURRENT"]
                                    ),
                                    "potential_environmental_impact_tco2e": float(
                                        row["ENVIRONMENT_IMPACT_POTENTIAL"]
                                    ),
                                    "floor_area_sqm": float(row["TOTAL_FLOOR_AREA"]),
                                    "yearly_primary_energy_use_kwh_sqm": float(
                                        row["ENERGY_CONSUMPTION_CURRENT"]
                                    ),
                                },
                            )
                        except DataError as e:
                            self.stderr.write(
                                f"Skipping row {row_number} due to data error: {e}.\n\nFull row: {row}"
                            )
                            continue
        self.stdout.write(f"Missing UPRNs in data: {them_missing_uprns}")
        self.stdout.write(f"Missing UPRNs in our DB: {us_missing_uprns}")

    def invalid_row(self, row, fields):
        for field in fields:
            if row[field] in ["", "INVALID!", "NO_DATA!", "N/A", "Not recorded"]:
                return True
        return False
