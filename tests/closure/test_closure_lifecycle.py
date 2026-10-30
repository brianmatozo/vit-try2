from fastapi.testclient import TestClient


def test_closure_open_and_get_active(client: TestClient):
    # Initially no active closure
    resp = client.get("/api/v1/closure/active")
    assert resp.status_code == 200
    assert resp.json() is None

    # Open closure with initial cash float
    open_resp = client.post(
        "/api/v1/closure/open",
        json={"initial_cash": 20000, "notes": "Apertura turno mañana"},
    )
    assert open_resp.status_code == 201
    data = open_resp.json()
    assert data["status"] == "open"
    assert data["initial_cash"] == 20000
    assert data["expected_cash"] == 20000
    assert data["opened_at"].endswith("Z")

    closure_id = data["id"]

    # Active endpoint now returns summary
    active_resp = client.get("/api/v1/closure/active")
    assert active_resp.status_code == 200
    active_data = active_resp.json()
    assert active_data["closure"]["id"] == closure_id
    assert active_data["closure"]["initial_cash"] == 20000
    assert active_data["discrepancy_status"] == "pending"


def test_cannot_open_duplicate_closure(client: TestClient):
    client.post("/api/v1/closure/open", json={"initial_cash": 15000})

    dup_resp = client.post("/api/v1/closure/open", json={"initial_cash": 10000})
    assert dup_resp.status_code == 409
    assert dup_resp.json()["code"] == "ACTIVE_CLOSURE_EXISTS"


def test_close_and_reconcile_arqueo(client: TestClient):
    open_resp = client.post("/api/v1/closure/open", json={"initial_cash": 30000})
    closure_id = open_resp.json()["id"]

    # Close with physical cash count (exact)
    close_resp = client.post(
        f"/api/v1/closure/{closure_id}/close",
        json={
            "counted_cash": 30000,
            "breakdown": {"10000": 3},
            "notes": "Caja cuadrada sin diferencias",
        },
    )
    assert close_resp.status_code == 200
    closed_data = close_resp.json()
    assert closed_data["status"] == "closed"
    assert closed_data["counted_cash"] == 30000
    assert closed_data["expected_cash"] == 30000
    assert closed_data["discrepancy"] == 0

    # Summary now reports 'exact'
    summary_resp = client.get(f"/api/v1/closure/{closure_id}/summary")
    assert summary_resp.status_code == 200
    assert summary_resp.json()["discrepancy_status"] == "exact"
