from django.contrib.auth import get_user_model
from django.db import models


class Toilet(models.Model):
    name = models.CharField("화장실명", max_length=120)
    address = models.CharField("주소", max_length=255)
    latitude = models.FloatField("위도")
    longitude = models.FloatField("경도")
    opening_hours = models.CharField("운영시간", max_length=120, default="상시 개방")
    is_open_24h = models.BooleanField("24시간", default=False)
    accessible = models.BooleanField("장애인 시설", default=False)
    provider = models.CharField("데이터 제공처", max_length=80, default="샘플 데이터")
    external_id = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ParkingLot(models.Model):
    toilet = models.ForeignKey(Toilet, on_delete=models.CASCADE, related_name="parking_lots")
    name = models.CharField("주차장명", max_length=120)
    latitude = models.FloatField("위도")
    longitude = models.FloatField("경도")
    capacity = models.PositiveIntegerField("주차면", default=0)
    is_public = models.BooleanField("공영", default=True)
    fee_type = models.CharField("요금", max_length=40, default="유료")

    def __str__(self):
        return self.name


class SafetyContext(models.Model):
    toilet = models.OneToOneField(Toilet, on_delete=models.CASCADE, related_name="safety")
    cctv_distance_m = models.PositiveIntegerField("최근접 CCTV 거리", null=True, blank=True)
    is_protected_zone = models.BooleanField("보호구역", default=False)
    enforcement_risk = models.PositiveSmallIntegerField("단속 위험도", default=20)

    def __str__(self):
        return f"{self.toilet.name} 안전 정보"


class UserReport(models.Model):
    class Type(models.TextChoices):
        OPEN = "OPEN", "정상 이용 가능"
        CLOSED = "CLOSED", "문이 닫혀 있음"
        PARKING_AVAILABLE = "PARKING_AVAILABLE", "주차 여유 있음"
        PARKING_DIFFICULT = "PARKING_DIFFICULT", "주차 어려움"
        ENFORCEMENT_SEEN = "ENFORCEMENT_SEEN", "단속 차량 목격"
        CLEAN = "CLEAN", "깨끗함"
        DIRTY = "DIRTY", "청결 불량"

    toilet = models.ForeignKey(Toilet, on_delete=models.CASCADE, related_name="reports")
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    report_type = models.CharField("제보 유형", max_length=30, choices=Type.choices)
    comment = models.CharField("한 줄 제보", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.toilet} - {self.get_report_type_display()}"
