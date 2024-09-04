from areas.models import Area, SpatialResolution
from building_performance.models import EPC
from consumption.models import Consumption
from django.db.models import Count, Q
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        grid_counts = Area.objects.aggregate(
            feeders_total=Count("id", Q(type=SpatialResolution.LV_FEEDER)),
            feeders_with_geometry=Count(
                "id", Q(type=SpatialResolution.LV_FEEDER, geometry__isnull=False)
            ),
        )

        data["total_consumption"] = Consumption.objects.count()
        data["total_feeders"] = grid_counts["feeders_total"]
        percentage_feeders_with_geometry = round(
            (grid_counts["feeders_with_geometry"] / grid_counts["feeders_total"]) * 100
        )
        total_epcs = EPC.objects.count()
        data["linked_epcs"] = total_epcs / 100 * percentage_feeders_with_geometry

        return data
