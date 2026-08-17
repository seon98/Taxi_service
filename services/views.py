import json
import math
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Toilet, UserReport
from .recommendation import recommend, score_toilet

DEFAULT_LAT, DEFAULT_LNG = 35.1595, 126.8526


def _location_params(request):
    try:
        lat = float(request.GET.get("latitude", DEFAULT_LAT))
        lng = float(request.GET.get("longitude", DEFAULT_LNG))
        radius = float(request.GET.get("radius", 3000))
    except (TypeError, ValueError):
        raise ValueError("위치와 검색 반경은 숫자여야 합니다.")
    if not all(math.isfinite(v) for v in (lat, lng, radius)) or not -90 <= lat <= 90 or not -180 <= lng <= 180:
        raise ValueError("올바른 위도와 경도를 입력해 주세요.")
    if not 300 <= radius <= 10000:
        raise ValueError("검색 반경은 300m에서 10km 사이여야 합니다.")
    return lat, lng, radius


def home(request):
    return render(request, "services/home.html", {"default_lat": DEFAULT_LAT, "default_lng": DEFAULT_LNG})


def recommendations_api(request):
    try:
        lat, lng, radius = _location_params(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    data_version = cache.get("recommendations:data-version", 1)
    cache_key = f"recommendations:v{data_version}:{round(lat, 3)}:{round(lng, 3)}:{round(radius)}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse({**cached, "cached": True})
    results = recommend(Toilet.objects.all(), lat, lng, radius)
    payload = {"count": len(results), "results": [r.to_dict() for r in results[:20]], "search": {"latitude": lat, "longitude": lng, "radius": radius}}
    cache.set(cache_key, payload, 45)
    return JsonResponse({**payload, "cached": False})


def toilet_detail_api(request, pk):
    toilet = get_object_or_404(Toilet.objects.prefetch_related("parking_lots", "reports").select_related("safety"), pk=pk)
    try:
        lat, lng, _ = _location_params(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    data = score_toilet(toilet, lat, lng).to_dict()
    data.update({"opening_hours": toilet.opening_hours, "accessible": toilet.accessible,
                 "facility_type": toilet.facility_type, "facility_type_label": toilet.get_facility_type_display(),
                 "access_info": toilet.access_info, "is_officially_designated": toilet.is_officially_designated,
                 "data_updated_at": toilet.updated_at.isoformat(),
                 "reports": [{"type": r.get_report_type_display(), "comment": r.comment, "created_at": r.created_at.isoformat()} for r in toilet.reports.all() if r.expires_at is None or r.expires_at > timezone.now()][:5]})
    return JsonResponse(data)


@require_POST
def create_report(request, pk):
    toilet = get_object_or_404(Toilet, pk=pk)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("올바른 JSON이 아닙니다.")
    report_type = payload.get("report_type")
    valid = dict(UserReport.Type.choices)
    if report_type not in valid:
        return HttpResponseBadRequest("올바른 제보 유형을 선택해 주세요.")
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    throttle_key = f"report:{session_key}:{pk}"
    if cache.get(throttle_key):
        return JsonResponse({"error": "같은 장소에는 1분 후 다시 제보할 수 있습니다."}, status=429)
    minutes = 30 if report_type == "ENFORCEMENT_SEEN" else 720 if report_type == "CLOSED" else 1440
    report = UserReport.objects.create(toilet=toilet, user=request.user if request.user.is_authenticated else None,
        report_type=report_type, comment=str(payload.get("comment", ""))[:200], expires_at=timezone.now() + timezone.timedelta(minutes=minutes))
    cache.set(throttle_key, True, 60)
    try:
        cache.incr("recommendations:data-version")
    except ValueError:
        cache.set("recommendations:data-version", 2, None)
    cache.set(throttle_key, True, 60)
    return JsonResponse({"ok": True, "message": "현장 제보가 반영되었습니다.", "report": report.get_report_type_display(), "expires_at": report.expires_at.isoformat()}, status=201)


def health(request):
    return JsonResponse({"status": "ok", "service": "Taxi Safe Toilet"})


def service_worker(request):
    script = '''self.addEventListener("install",event=>self.skipWaiting());
self.addEventListener("activate",event=>event.waitUntil(self.clients.claim()));
self.addEventListener("notificationclick",event=>{event.notification.close();event.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(clients=>clients[0]?clients[0].focus():self.clients.openWindow("/")))});'''
    response = HttpResponse(script, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response
