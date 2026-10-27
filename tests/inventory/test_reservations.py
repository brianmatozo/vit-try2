from fastapi.testclient import TestClient

from tests.inventory.conftest import create_test_product


class TestInventoryReservationFulfill:
    def test_reserve_and_fulfill_delivery_order(self, client: TestClient):
        # 1,200g stock, 500g buffer -> 700g virtual available
        product_id = create_test_product(
            client, current_stock=1200, min_safety_buffer=500
        )

        # Attempting to reserve 800g exceeds 700g virtual stock -> rejected
        r_fail = client.post(
            "/api/v1/inventory/reserve",
            json={
                "product_id": product_id,
                "quantity": 800,
                "order_reference_id": "PEYA-9001",
            },
        )
        assert r_fail.status_code == 400

        # Reserving 600g succeeds
        r_ok = client.post(
            "/api/v1/inventory/reserve",
            json={
                "product_id": product_id,
                "quantity": 600,
                "order_reference_id": "PEYA-9001",
            },
        )
        assert r_ok.status_code == 200
        prod = r_ok.json()
        assert prod["reserved_stock"] == 600
        # Virtual stock: max(0, 1200 - 600 - 500) = 100
        assert prod["virtual_stock"] == 100

        # Fulfill order (picked and dispatched)
        f_resp = client.post(
            "/api/v1/inventory/fulfill",
            json={
                "product_id": product_id,
                "quantity": 600,
                "order_reference_id": "PEYA-9001",
            },
        )
        assert f_resp.status_code == 200
        entry = f_resp.json()
        assert entry["movement_type"] == "delivery_fulfilled"
        assert entry["quantity_delta"] == -600
        assert entry["balance_after"] == 600

        # Verify stock and reservation cleared
        prod_after = client.get(f"/api/v1/products/{product_id}").json()
        assert prod_after["current_stock"] == 600
        assert prod_after["reserved_stock"] == 0

    def test_reserve_and_release_cancelled_order(self, client: TestClient):
        product_id = create_test_product(
            client, current_stock=2000, min_safety_buffer=0
        )

        client.post(
            "/api/v1/inventory/reserve",
            json={
                "product_id": product_id,
                "quantity": 500,
                "order_reference_id": "RAPPI-1234",
            },
        )

        rel_resp = client.post(
            "/api/v1/inventory/release",
            json={
                "product_id": product_id,
                "quantity": 500,
                "order_reference_id": "RAPPI-1234",
            },
        )
        assert rel_resp.status_code == 200
        assert rel_resp.json()["reserved_stock"] == 0
