import os
import re

from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand

from areas.models import Area


class CustomLayerMapping(LayerMapping):
    def __init__(self, *args, **kwargs):
        self.custom = kwargs.pop("custom", {})
        super(CustomLayerMapping, self).__init__(*args, **kwargs)

    def feature_kwargs(self, feature):
        kwargs = super(CustomLayerMapping, self).feature_kwargs(feature)
        kwargs.update(self.custom)
        return kwargs


class Command(BaseCommand):
    help = "Load postcode sectors from MHL's GeoJSON file"

    def add_arguments(self, parser):
        parser.add_argument("directory", type=str)
        parser.add_argument("type", type=str)

    def handle(self, *args, **options):
        mapping = {
            "name": "sector",
            "geometry": "MULTIPOLYGON",
        }
        custom = {
            "type": options["type"],
        }

        for root, dirs, filenames in os.walk(options["directory"]):
            dirs.sort()
            filenames.sort()
            for filename in filenames:
                m = re.search(r"^(.*)\.geojson$", filename)
                if not m:
                    continue
                sector = m.group(1)
                full_filename = os.path.join(root, filename)

                self.stdout.write(f"Importing {sector} from {filename}")

                lm = CustomLayerMapping(
                    model=Area, data=full_filename, mapping=mapping, custom=custom
                )
                lm.save(strict=True, verbose=True)
