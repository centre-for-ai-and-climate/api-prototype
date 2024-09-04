import json
import os
import re

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand
from uk_postcodes_parsing import ukpostcode

from areas.models import Area, SpatialResolution


class CustomLayerMapping(LayerMapping):
    def __init__(self, *args, **kwargs):
        self.custom = kwargs.pop("custom", {})
        super(CustomLayerMapping, self).__init__(*args, **kwargs)

    def feature_kwargs(self, feature):
        kwargs = super(CustomLayerMapping, self).feature_kwargs(feature)
        kwargs.update(self.custom)
        return kwargs


class Command(BaseCommand):
    help = "Load postcode units (individual postcodes) from MHL's GeoJSON file"

    def add_arguments(self, parser):
        parser.add_argument("directory", type=str)

    def handle(self, *args, **options):
        # Can't use standard LayerMapping as we need to set the parent of each
        # postcode to the sector it belongs to dynamically by parsing the geojson

        sectors = {}
        for sector in Area.objects.filter(type=SpatialResolution.POSTCODE_SECTOR).only(
            "name", "id"
        ):
            sectors[sector.name] = sector

        batch = []
        batch_size = 10000
        row_number = 0

        for root, dirs, filenames in os.walk(options["directory"]):
            dirs.sort()
            filenames.sort()
            for filename in filenames:
                m = re.search(r"^(.*)\.geojson$", filename)
                if not m:
                    continue
                district = m.group(1)
                full_filename = os.path.join(root, filename)

                self.stdout.write(f"Importing {district} from {filename}")

                postcodes = json.load(open(full_filename))["features"]

                for postcode in postcodes:
                    row_number += 1
                    sector = ukpostcode.parse(
                        postcode["properties"]["postcodes"]
                    ).sector
                    area = Area(
                        name=postcode["properties"]["postcodes"],
                        geometry=self.parse_geometry(postcode["geometry"]),
                        type=SpatialResolution.POSTCODE,
                        parent=sectors[sector],
                    )

                    batch.append(area)

                    if len(batch) >= batch_size:
                        self.save_batch(batch, row_number)
                        batch = []

        if len(batch) > 0:
            self.save_batch(batch, row_number)

    def parse_geometry(self, geojson):
        geom = GEOSGeometry(json.dumps(geojson))
        if isinstance(geom, MultiPolygon):
            return geom
        else:
            return MultiPolygon([geom])

    def save_batch(self, batch, row_number):
        Area.objects.bulk_create(batch)
        self.stdout.write(f"Imported up to {row_number}")
