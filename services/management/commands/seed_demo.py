from django.core.management.base import BaseCommand
from services.models import ParkingLot, SafetyContext, Toilet

DATA = [
    ("광주광역시청 공중화장실", "광주 서구 내방로 111", 35.1601, 126.8515, "24시간", True, 120, False, 75, "시청 공영주차장", 35.1604, 126.8509, 240),
    ("상무시민공원 화장실", "광주 서구 상무공원로 101", 35.1532, 126.8419, "06:00 - 23:00", False, 260, False, 15, "상무공원 주차장", 35.1536, 126.8425, 84),
    ("5·18기념공원 화장실", "광주 서구 내방로 152", 35.1578, 126.8576, "06:00 - 22:00", False, 65, False, 45, "기념공원 공영주차장", 35.1583, 126.8580, 62),
    ("운천저수지 화장실", "광주 서구 운천로 165", 35.1504, 126.8617, "05:00 - 24:00", False, 42, True, 70, None, None, None, 0),
    ("김대중컨벤션센터 화장실", "광주 서구 상무누리로 30", 35.1468, 126.8405, "08:00 - 22:00", False, 340, False, 10, "컨벤션센터 제1주차장", 35.1471, 126.8398, 412),
]

class Command(BaseCommand):
    help = "광주 MVP 시연용 데이터를 생성합니다."
    def handle(self, *args, **options):
        for name,address,lat,lng,hours,all_day,cctv,zone,risk,pname,plat,plng,capacity in DATA:
            open_names = {"광주광역시청 공중화장실", "김대중컨벤션센터 화장실"}
            facility_type = Toilet.FacilityType.OPEN if name in open_names else Toilet.FacilityType.PUBLIC
            toilet,_=Toilet.objects.update_or_create(name=name,defaults={"address":address,"latitude":lat,"longitude":lng,"opening_hours":hours,"is_open_24h":all_day,"accessible":True,"facility_type":facility_type,"access_info":"시설 운영시간 내 누구나 이용 가능" if facility_type == Toilet.FacilityType.OPEN else "외부에서 바로 출입 가능","is_officially_designated":True,"provider":"광주광역시 MVP"})
            SafetyContext.objects.update_or_create(toilet=toilet,defaults={"cctv_distance_m":cctv,"is_protected_zone":zone,"enforcement_risk":risk})
            if pname: ParkingLot.objects.update_or_create(toilet=toilet,name=pname,defaults={"latitude":plat,"longitude":plng,"capacity":capacity,"is_public":True})
        self.stdout.write(self.style.SUCCESS(f"시연용 화장실 {len(DATA)}곳을 준비했습니다."))
