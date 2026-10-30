from fastapi.testclient import TestClient

from tests.inventory.conftest import create_test_product


def test_pos_checkout_rejected_when_register_closed(client: TestClient):
    prod_id = create_test_product(client, current_stock=1000)

    # Attempt batch sale without any open closure
    resp = client.post(
        "/api/v1/inventory/sale-pos/batch",
        json={
            "ticket_reference_id": "STRICT-POS-01",
            "items": [{"product_id": prod_id, "quantity": 100}],
        },
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "REGISTER_CLOSED"


def test_pos_checkout_allowed_and_tracked_when_register_open(client: TestClient):
    # Open register
    open_resp = client.post("/api/v1/closure/open", json={"initial_cash": 10000})
    closure_id = open_resp.json()["id"]

    prod_id = create_test_product(
        client, current_stock=1000, unit_price=1500, product_type="discrete"
    )

    # Checkout 2 units (2 * $1500 = $3000) with cash
    sale_resp = client.post(
        "/api/v1/inventory/sale-pos/batch",
        json={
            "ticket_reference_id": "STRICT-POS-02",
            "items": [{"product_id": prod_id, "quantity": 2}],
            "payment_method": "cash",
            "cash_tendered": 5000,
            "change_returned": 2000,
        },
    )
    assert sale_resp.status_code == 200

    # Verify closure stats updated
    active = client.get("/api/v1/closure/active").json()["closure"]
    assert active["id"] == closure_id
    assert active["cash_sales_amount"] == 3000
    assert active["total_sales_amount"] == 3000
    assert active["expected_cash"] == 13000  # 10,000 + 3,000

    # Verify POSTicket recorded
    tickets = client.get(f"/api/v1/closure/{closure_id}/tickets").json()
    assert len(tickets) == 1
    assert tickets[0]["ticket_id"] == "STRICT-POS-02"
    assert tickets[0]["payment_method"] == "cash"
    assert tickets[0]["total_amount"] == 3000
    assert tickets[0]["cash_tendered"] == 5000
    assert tickets[0]["change_returned"] == 2000
