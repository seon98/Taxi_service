import json
from datetime import time
from unittest.mock import patch
from django.test import TestCase
from .models import ParkingLot, SafetyContext, Toilet, UserReport
from .recommendation import distance_m, is_open_now, score_toilet

class RecommendationTests(TestCase):
    def setUp(self):
        self.toilet=Toilet.objects.create(name="테스트 화장실",address="광주",latitude=35.1595,longitude=126.8526,is_open_24h=True)
        ParkingLot.objects.create(toilet=self.toilet,name="공영주차장",latitude=35.1596,longitude=126.8526,capacity=20)
        SafetyContext.objects.create(toilet=self.toilet,cctv_distance_m=400,enforcement_risk=5)
    def test_distance_same_point_is_zero(self): self.assertEqual(distance_m(35,126,35,126),0)
    def test_score_is_explainable(self):
        result=score_toilet(self.toilet,35.1595,126.8526)
        self.assertGreaterEqual(result.safe_score,80);self.assertIn("parking",result.factors)
    def test_recommendation_api(self):
        response=self.client.get('/api/v1/toilets/recommendations/',{'latitude':35.1595,'longitude':126.8526})
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['count'],1)
    def test_report_api(self):
        response=self.client.post(f'/api/v1/toilets/{self.toilet.pk}/reports/',data=json.dumps({'report_type':'OPEN'}),content_type='application/json')
        self.assertEqual(response.status_code,201);self.assertEqual(UserReport.objects.count(),1)
    def test_report_is_throttled_per_session(self):
        url=f'/api/v1/toilets/{self.toilet.pk}/reports/'
        self.client.post(url,data=json.dumps({'report_type':'OPEN'}),content_type='application/json')
        response=self.client.post(url,data=json.dumps({'report_type':'CLOSED'}),content_type='application/json')
        self.assertEqual(response.status_code,429)
    def test_invalid_coordinates_are_rejected(self):
        response=self.client.get('/api/v1/toilets/recommendations/',{'latitude':999,'longitude':126})
        self.assertEqual(response.status_code,400)
    def test_overnight_hours(self):
        self.toilet.is_open_24h=False;self.toilet.opening_hours='22:00 - 05:00'
        with patch('services.recommendation.timezone.localtime') as localtime:
            localtime.return_value.time.return_value=time(2,0)
            self.assertTrue(is_open_now(self.toilet))
    def test_multiple_reports_use_consensus(self):
        UserReport.objects.create(toilet=self.toilet,report_type='OPEN')
        UserReport.objects.create(toilet=self.toilet,report_type='PARKING_AVAILABLE')
        result=score_toilet(self.toilet,35.1595,126.8526)
        self.assertEqual(result.report_summary['positive'],2)
