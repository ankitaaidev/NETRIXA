from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_summary_shape_and_values():
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["totalEvents"] == 207
    assert body["criticalEvents"] >= 5
    assert body["persistentSources"] >= 10


def test_list_events_pagination():
    resp = client.get("/api/events?page=1&pageSize=5")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 5
    assert body["total"] == 207
    assert body["page"] == 1
    assert body["pageSize"] == 5


def test_list_events_filter_by_risk_level():
    resp = client.get("/api/events?riskLevel=CRITICAL&pageSize=200")
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["riskLevel"] == "CRITICAL" for item in body["items"])
    assert len(body["items"]) >= 5


def test_list_events_filter_by_state():
    resp = client.get("/api/events?state=Punjab&pageSize=200")
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["state"] == "Punjab" for item in body["items"])
    assert len(body["items"]) > 0


def test_get_event_detail_scenario_c():
    resp = client.get("/api/events/NTX-IND-00003")
    assert resp.status_code == 200
    body = resp.json()
    assert body["classification"] == "Potential Industrial Fire"
    assert body["riskLevel"] == "CRITICAL"
    assert len(body["historicalData"]) == 90


def test_get_event_detail_404():
    resp = client.get("/api/events/NTX-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_event_history_endpoint():
    resp = client.get("/api/events/NTX-IND-00001/history")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 90
    assert "date" in body[0] and "intensity" in body[0]


def test_analyze_event_returns_consistent_result():
    resp = client.post("/api/events/NTX-IND-00001/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["classification"] == "Persistent Industrial Thermal Source"
    assert body["riskLevel"] == "LOW"


def test_analyze_nonexistent_event_404():
    resp = client.post("/api/events/NTX-FAKE-00000/analyze")
    assert resp.status_code == 404


def test_submit_feedback_valid():
    resp = client.post(
        "/api/events/NTX-IND-00002/feedback",
        json={"decision": "CONFIRMED", "analystNote": "test note"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "CONFIRMED"


def test_submit_feedback_invalid_decision_422():
    resp = client.post("/api/events/NTX-IND-00002/feedback", json={"decision": "NOT_A_REAL_DECISION"})
    assert resp.status_code == 422


def test_priority_center_sorted_descending():
    resp = client.get("/api/priority?pageSize=20")
    assert resp.status_code == 200
    body = resp.json()
    scores = [item["riskScore"] for item in body["items"]]
    assert scores == sorted(scores, reverse=True)


def test_facilities_list_and_detail():
    resp = client.get("/api/facilities")
    assert resp.status_code == 200
    facilities = resp.json()
    assert len(facilities) == 30

    facility_id = facilities[0]["facilityId"]
    detail_resp = client.get(f"/api/facilities/{facility_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["facilityId"] == facility_id


def test_facility_detail_404():
    resp = client.get("/api/facilities/FAC-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_alerts_list_and_filter():
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    all_alerts = resp.json()
    assert len(all_alerts) > 0
    assert all(a["severity"] in ("HIGH", "CRITICAL") for a in all_alerts)

    active_resp = client.get("/api/alerts?status=ACTIVE")
    assert all(a["status"] == "ACTIVE" for a in active_resp.json())


def test_resolve_alert_and_idempotent_404_after_fake_id():
    alerts = client.get("/api/alerts?status=ACTIVE").json()
    assert len(alerts) > 0
    alert_id = alerts[0]["id"]

    resolve_resp = client.post(f"/api/alerts/{alert_id}/resolve")
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert resolve_resp.json()["resolvedAt"] is not None


def test_resolve_nonexistent_alert_404():
    resp = client.post("/api/alerts/FAKE-ALERT-ID/resolve")
    assert resp.status_code == 404


def test_map_events_returns_valid_geojson():
    resp = client.get("/api/map/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 207
    feature = body["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert len(feature["geometry"]["coordinates"]) == 2


def test_map_facilities_returns_valid_geojson():
    resp = client.get("/api/map/facilities")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 30


def test_generate_report_for_analyzed_event():
    resp = client.post("/api/reports/events/NTX-IND-00003")
    assert resp.status_code == 200
    body = resp.json()
    assert "disclaimer" in body
    assert "prototype" in body["disclaimer"].lower()
    assert body["event"]["classification"] == "Potential Industrial Fire"


def test_generate_report_404_for_missing_event():
    resp = client.post("/api/reports/events/NTX-FAKE-00000")
    assert resp.status_code == 404


def test_cors_headers_present():
    resp = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
