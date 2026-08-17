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
- 1·3·5·10km 검색 반경과 안심/거리 정렬
- 장애인 시설·주차장·운영 여부·저장 장소 필터
- 여러 현장 제보의 합의를 반영하는 점수와 반복 제보 제한
- 입력값 검증, 검색 결과 캐시, 네트워크 오류 복구

개발 환경은 설치 장벽을 낮추기 위해 SQLite와 위·경도 필드를 사용합니다. 운영 전환 시 모델의 위치 필드를 GeoDjango `PointField`로 교체하고 PostgreSQL/PostGIS 공간 인덱스를 적용하는 것이 다음 단계입니다.

## 다음 개발 우선순위

1. 광주 공공데이터 Provider와 수집 이력 모델을 연결해 시연 데이터를 실제 데이터로 교체
2. PostgreSQL/PostGIS의 반경 검색과 공간 인덱스로 전국 데이터 검색 성능 확보
3. 기사 인증, 제보 확인·반박, 사용자 신뢰 등급으로 크라우드소싱 품질 강화
4. Redis·Celery로 데이터 동기화, 제보 만료, 캐시를 다중 서버 환경에 적용
5. TMAP·카카오내비 딥링크 선택, PWA 설치와 오프라인 최근 결과 제공
6. 개인정보 동의, 위치 로그 비저장 검증, 모니터링과 장애 알림을 포함한 운영 준비
