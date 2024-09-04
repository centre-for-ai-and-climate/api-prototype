"""
URL configuration for energy_system_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from areas.views import AreaDetailView, area_geojson_view
from building_performance.views import epc_geojson_view
from django.contrib import admin
from django.urls import path

from energy_system_api.views import IndexView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", IndexView.as_view(), name="index"),
    path("areas/<int:pk>", AreaDetailView.as_view()),
    # Hacky GEOJSON views to allow us to map stuff quickly
    path("areas.geojson", area_geojson_view),
    path("epcs.geojson", epc_geojson_view),
]
