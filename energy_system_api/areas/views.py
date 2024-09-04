from building_performance.models import EPC
from consumption.models import Consumption
from django.contrib.gis.geos import Polygon
from django.core.serializers import serialize
from django.db.models import Avg, Count, Max, Min
from django.http import HttpResponse, JsonResponse
from django.views.generic import DetailView

from areas.models import Area, SpatialResolution


class AreaDetailView(DetailView):
    model = Area
    context_object_name = "area"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["boundary"] = serialize(
            "geojson", [self.object], geometry_field="geometry", fields="name"
        )

        consumption_stats = Consumption.objects.filter(area=data["area"]).aggregate(
            Min("start_timestamp"),
            Max("end_timestamp"),
            Avg("number_of_meters"),
            Count("id"),
        )

        data["consumption"] = {
            "earliest": consumption_stats["start_timestamp__min"],
            "latest": consumption_stats["end_timestamp__max"],
            "meters": consumption_stats["number_of_meters__avg"],
            "records": consumption_stats["id__count"],
        }

        if data["area"].geometry is not None:
            epc_stats = EPC.objects.filter(
                uprn__location__within=data["area"].geometry
            ).aggregate(
                Min("timestamp"),
                Max("timestamp"),
                Avg("floor_area_sqm"),
                Count("id"),
            )

            data["epcs"] = {
                "earliest": epc_stats["timestamp__min"],
                "latest": epc_stats["timestamp__max"],
                "avg_floor_area": epc_stats["floor_area_sqm__avg"],
                "records": epc_stats["id__count"],
            }
        return data


def area_geojson_view(request):
    bbox = request.GET.get("bbox")

    if bbox:
        bbox = [float(coord) for coord in bbox.split(",")]
        areas = Area.objects.filter(
            geometry__bboverlaps=Polygon.from_bbox(bbox),
            type=SpatialResolution.LV_FEEDER,
        )

        return HttpResponse(
            serialize(
                "geojson", areas, geometry_field="geometry", fields=["name", "id"]
            ),
            content_type="application/json",
        )
    return JsonResponse({})
