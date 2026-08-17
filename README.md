# Taxi Safe Toilet

택시·이동 노동자가 현재 위치 주변에서 이용 가능하고 정차하기 상대적으로 안전한 화장실을 찾도록 돕는 Django MVP입니다.

## 실행

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000`을 여세요. 위치 권한을 허용하면 현재 위치를, 거부하면 광주광역시청 주변 시연 데이터를 사용합니다.

## 구현 범위

- 현재 위치 기반 반경 3km 검색
- 운영시간, 주차 접근성, CCTV, 보호구역, 현장 제보를 조합한 설명 가능한 점수
- OpenStreetMap 지도와 추천 TOP 목록
- 카카오맵 목적지 연결
- 만료 시간이 있는 익명 현장 제보
- 화장실·주차장·안전정보·제보 Django Admin
- JSON API와 health endpoint

개발 환경은 설치 장벽을 낮추기 위해 SQLite와 위·경도 필드를 사용합니다. 운영 전환 시 모델의 위치 필드를 GeoDjango `PointField`로 교체하고 PostgreSQL/PostGIS 공간 인덱스를 적용하는 것이 다음 단계입니다.
