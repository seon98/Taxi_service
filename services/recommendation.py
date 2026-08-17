from dataclasses import asdict, dataclass
from math import asin, cos, radians, sin, sqrt
from django.utils import timezone


def distance_m(lat1, lng1, lat2, lng2):
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 12_742_000 * asin(sqrt(a))


def is_open_now(toilet):
    if toilet.is_open_24h:
        return True
    try:
        start, end = toilet.opening_hours.replace(" ", "").split("-")
        now = timezone.localtime().time()
        return timezone.datetime.strptime(start, "%H:%M").time() <= now <= timezone.datetime.strptime(end, "%H:%M").time()
    except (ValueError, AttributeError):
        return True


@dataclass
class Recommendation:
    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    distance_meters: int
    is_open: bool
    safe_score: int
    risk_level: str
    parking: dict
    factors: dict
    latest_report: str | None

    def to_dict(self):
        return asdict(self)


def score_toilet(toilet, latitude, longitude):
    distance = round(distance_m(latitude, longitude, toilet.latitude, toilet.longitude))
    opened = is_open_now(toilet)
    distance_score = max(0, 100 - distance / 30)
    availability_score = 100 if opened else 15
    parking = min(toilet.parking_lots.all(), key=lambda p: distance_m(p.latitude, p.longitude, toilet.latitude, toilet.longitude), default=None)
    parking_distance = round(distance_m(parking.latitude, parking.longitude, toilet.latitude, toilet.longitude)) if parking else None
    parking_score = max(20, 100 - (parking_distance or 500) / 6) if parking else 20
    safety = getattr(toilet, "safety", None)
    cctv_distance = safety.cctv_distance_m if safety else None
    enforcement_score = 100
    if cctv_distance is not None:
        enforcement_score = 45 if cctv_distance <= 50 else 70 if cctv_distance <= 100 else 90
    if safety:
        enforcement_score -= safety.enforcement_risk * .25
        if safety.is_protected_zone:
            enforcement_score -= 30
    active_reports = toilet.reports.filter(expires_at__gt=timezone.now()) | toilet.reports.filter(expires_at__isnull=True)
    latest = active_reports.first()
    report_score = 80
    if latest:
        report_score += 15 if latest.report_type in {"OPEN", "PARKING_AVAILABLE", "CLEAN"} else -35
    score = round(distance_score * .20 + availability_score * .20 + parking_score * .25 + max(0, enforcement_score) * .20 + report_score * .15)
    risk = "LOW" if score >= 80 else "MEDIUM" if score >= 60 else "HIGH"
    return Recommendation(toilet.id, toilet.name, toilet.address, toilet.latitude, toilet.longitude, distance, opened, score, risk,
        {"available": parking is not None, "name": parking.name if parking else None, "distance_meters": parking_distance, "capacity": parking.capacity if parking else None},
        {"distance": round(distance_score), "availability": availability_score, "parking": round(parking_score), "enforcement": round(max(0, enforcement_score)), "reports": report_score,
         "cctv_distance_m": cctv_distance, "protected_zone": safety.is_protected_zone if safety else False},
        latest.get_report_type_display() if latest else None)


def recommend(queryset, latitude, longitude, radius=3000):
    results = [score_toilet(t, latitude, longitude) for t in queryset.prefetch_related("parking_lots", "reports").select_related("safety")]
    return sorted((r for r in results if r.distance_meters <= radius), key=lambda r: (-r.safe_score, r.distance_meters))
