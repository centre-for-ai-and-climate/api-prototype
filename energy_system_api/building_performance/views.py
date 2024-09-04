import json

from django.contrib.gis.geos import Polygon
from django.http import JsonResponse

from .models import EPC


# Create your views here.
def epc_geojson_view(request):
    bbox = request.GET.get("bbox")

    if bbox:
        bbox = [float(coord) for coord in bbox.split(",")]
        epcs = (
            EPC.objects.select_related("uprn")
            .filter(uprn__location__within=Polygon.from_bbox(bbox))
            .only("uprn__location", "id")
            .values("uprn__location", "id")
        )

        return JsonResponse(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": json.loads(epc["uprn__location"].geojson),
                        "properties": {"id": epc["id"]},
                    }
                    for epc in epcs
                ],
            },
        )
    return JsonResponse({})
