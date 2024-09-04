import gc

from django.contrib.gis.db.models import Union
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.management.base import BaseCommand
from django.db.models import Count

from areas.models import Area, SpatialResolution


class Command(BaseCommand):
    help = "Augment Secondary Substation areas with LV Feeder geometries"

    # From https://djangosnippets.org/snippets/1949/
    def queryset_iterator(self, queryset, chunksize=1000):
        """''
        Iterate over a Django Queryset ordered by the primary key

        This method loads a maximum of chunksize (default: 1000) rows in it's
        memory at the same time while django normally would load all rows in it's
        memory. Using the iterator() method only causes it to not preload all the
        classes.

        Note that the implementation of the iterator does not support ordered query sets.
        """
        pk = 0
        last_pk = queryset.order_by("-pk")[0].pk
        queryset = queryset.order_by("pk")
        while pk < last_pk:
            for row in queryset.filter(pk__gt=pk)[:chunksize]:
                pk = row.pk
                yield row
            gc.collect()

    def handle(self, *args, **options):
        # Some of our LV feeders have areas, so with those we can add areas to their
        # parent substations.

        # Can't do a simple queryset or iterator because it will use too much memory
        batch = []
        batch_size = 1000
        row_number = 0

        for substation in self.queryset_iterator(
            Area.objects.filter(type=SpatialResolution.SECONDARY_SUBSTATION)
        ):
            row_number += 1
            lv_feeders = Area.objects.filter(
                parent=substation,
                type=SpatialResolution.LV_FEEDER,
                geometry__isnull=False,
            ).aggregate(Union("geometry"), Count("id"))

            if lv_feeders["id__count"] == 0:
                self.stderr.write(
                    f"Skipping {substation} as no LV feeder geometries found to combine"
                )
                continue

            substation.geometry = self.fix_multipolygon(lv_feeders["geometry__union"])
            batch.append(substation)

            if len(batch) >= batch_size:
                self.save_batch(batch, row_number)
                batch = []

        if len(batch) > 0:
            self.save_batch(batch, row_number)

    def fix_multipolygon(self, geom):
        if isinstance(geom, MultiPolygon):
            return geom
        elif isinstance(geom, Polygon):
            return MultiPolygon([geom])
        else:
            self.stderr.write(f"Unexpected geometry type {type(geom)}")
            return None

    def save_batch(self, batch, row_number):
        Area.objects.bulk_update(batch, ["geometry"])
        self.stdout.write(f"Processed up to {row_number}")
