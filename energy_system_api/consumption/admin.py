from django.contrib import admin

from consumption.models import Consumption


class ConsumptionAdmin(admin.ModelAdmin):
    list_display = (
        "area__name",
        "start_timestamp",
        "end_timestamp",
        "kwh",
        "number_of_meters",
    )
    list_filter = (
        "spatial_resolution",
        "temporal_resolution",
    )
    search_fields = ("area__name",)
    ordering = ("area__name", "start_timestamp")
    raw_id_fields = ("area",)


admin.site.register(Consumption, ConsumptionAdmin)
