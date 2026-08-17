from django.contrib import admin
from .models import ParkingLot, SafetyContext, Toilet, UserReport


class ParkingInline(admin.TabularInline):
    model = ParkingLot
    extra = 0


class SafetyInline(admin.StackedInline):
    model = SafetyContext
    extra = 0


@admin.register(Toilet)
class ToiletAdmin(admin.ModelAdmin):
    list_display = ("name", "facility_type", "address", "opening_hours", "is_open_24h", "is_officially_designated", "provider")
    search_fields = ("name", "address")
    list_filter = ("facility_type", "is_open_24h", "accessible", "is_officially_designated", "provider")
    inlines = (ParkingInline, SafetyInline)


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ("toilet", "report_type", "comment", "created_at", "expires_at")
    list_filter = ("report_type", "created_at")

admin.site.register(ParkingLot)
admin.site.register(SafetyContext)
