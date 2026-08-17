from django.urls import path
from . import views

app_name = "services"
urlpatterns = [
    path("", views.home, name="home"),
    path("api/v1/toilets/recommendations/", views.recommendations_api, name="recommendations"),
    path("api/v1/toilets/<int:pk>/", views.toilet_detail_api, name="detail"),
    path("api/v1/toilets/<int:pk>/reports/", views.create_report, name="report"),
    path("health/", views.health, name="health"),
]
