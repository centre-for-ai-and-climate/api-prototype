from django.contrib import admin

from building_performance.models import EPC


class EPCAdmin(admin.ModelAdmin):
    list_display = (
        "uprn__name",
        "timestamp",
    )
    search_fields = ("uprn__name",)
    ordering = ("uprn__name", "timestamp")
    raw_id_fields = ("uprn",)


admin.site.register(EPC, EPCAdmin)
