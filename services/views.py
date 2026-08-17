import json
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Toilet, UserReport
from .recommendation import recommend, score_toilet

DEFAULT_LAT, DEFAULT_LNG = 35.1595, 126.8526


def home(request):
    return render(request, "services/home.html", {"default_lat": DEFAULT_LAT, "default_lng": DEFAULT_LNG})


def recommendations_api(request):
    try:
        lat = float(request.GET.get("latitude", DEFAULT_LAT))
        lng = float(request.GET.get("longitude", DEFAULT_LNG))
        radius = min(float(request.GET.get("radius", 3000)), 10000)
    except ValueError:
        return HttpResponseBadRequest("위치와 검색 반경은 숫자여야 합니다.")
    results = recommend(Toilet.objects.all(), lat, lng, radius)
    return JsonResponse({"count": len(results), "results": [r.to_dict() for r in results[:20]]})


def toilet_detail_api(request, pk):
    toilet = get_object_or_404(Toilet.objects.prefetch_related("parking_lots", "reports").select_related("safety"), pk=pk)
    lat = float(request.GET.get("latitude", DEFAULT_LAT))
    lng = float(request.GET.get("longitude", DEFAULT_LNG))
    data = score_toilet(toilet, lat, lng).to_dict()
    data.update({"opening_hours": toilet.opening_hours, "accessible": toilet.accessible,
                 "reports": [{"type": r.get_report_type_display(), "comment": r.comment, "created_at": r.created_at.isoformat()} for r in toilet.reports.all()[:5]]})
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
    minutes = 30 if report_type == "ENFORCEMENT_SEEN" else 720 if report_type == "CLOSED" else 1440
    report = UserReport.objects.create(toilet=toilet, user=request.user if request.user.is_authenticated else None,
        report_type=report_type, comment=str(payload.get("comment", ""))[:200], expires_at=timezone.now() + timezone.timedelta(minutes=minutes))
    return JsonResponse({"ok": True, "message": "현장 제보가 반영되었습니다.", "report": report.get_report_type_display()}, status=201)


def health(request):
    return JsonResponse({"status": "ok", "service": "Taxi Safe Toilet"})
