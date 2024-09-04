from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from areas.models import Area


class AreaAdmin(GISModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type",)
    search_fields = ("name",)
    ordering = ("type", "name")
    raw_id_fields = ("parent",)


admin.site.register(Area, AreaAdmin)
