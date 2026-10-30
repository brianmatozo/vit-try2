from fastapi.testclient import TestClient


def test_cash_in_and_cash_out_movements(client: TestClient):
    open_resp = client.post("/api/v1/closure/open", json={"initial_cash": 20000})
    closure_id = open_resp.json()["id"]

    # 1. Cash In: Adding $5,000 for small change
    in_resp = client.post(
        f"/api/v1/closure/{closure_id}/movements",
        json={
            "movement_type": "cash_in",
            "amount": 5000,
            "reason": "Cambio de billetes chicos",
        },
    )
    assert in_resp.status_code == 201
    in_data = in_resp.json()
    assert in_data["amount"] == 5000
    assert in_data["movement_type"] == "cash_in"

    # Verify expected cash increased to 25,000
    active = client.get("/api/v1/closure/active").json()["closure"]
    assert active["cash_in_amount"] == 5000
    assert active["expected_cash"] == 25000

    # 2. Cash Out: $3,000 for cleaning supplies
    out_resp = client.post(
        f"/api/v1/closure/{closure_id}/movements",
        json={
            "movement_type": "cash_out",
            "amount": 3000,
            "reason": "Artículos de limpieza y bolsas",
        },
    )
    assert out_resp.status_code == 201

    # Verify expected cash decreased to 22,000
    active = client.get("/api/v1/closure/active").json()["closure"]
    assert active["cash_out_amount"] == 3000
    assert active["expected_cash"] == 22000

    # 3. List movements
    list_resp = client.get(f"/api/v1/closure/{closure_id}/movements")
    assert list_resp.status_code == 200
    movements = list_resp.json()
    assert len(movements) == 2
    assert movements[0]["movement_type"] == "cash_in"
    assert movements[1]["movement_type"] == "cash_out"
