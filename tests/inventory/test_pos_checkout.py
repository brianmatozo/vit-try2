from fastapi.testclient import TestClient

from tests.inventory.conftest import create_test_product


class TestPOSSale:
    def test_pos_sale_deducts_with_physical_priority(self, client: TestClient):
        product_id = create_test_product(client, current_stock=3000)

        resp = client.post(
            "/api/v1/inventory/sale-pos",
            json={
                "product_id": product_id,
                "quantity": 400,
                "ticket_reference_id": "TICKET-7788",
            },
        )
        assert resp.status_code == 200
        entry = resp.json()
        assert entry["movement_type"] == "sale_pos"
        assert entry["quantity_delta"] == -400
        assert entry["balance_after"] == 2600
        assert entry["created_at"].endswith("Z")

        prod = client.get(f"/api/v1/products/{product_id}").json()
        assert prod["current_stock"] == 2600


class TestPOSBatchSale:
    def test_pos_batch_sale_multi_item_success(self, client: TestClient):
        p1 = create_test_product(client, sku="BATCH-P1", current_stock=1000)
        p2 = create_test_product(client, sku="BATCH-P2", current_stock=2000)

        resp = client.post(
            "/api/v1/inventory/sale-pos/batch",
            json={
                "ticket_reference_id": "TICKET-BATCH-01",
                "items": [
                    {"product_id": p1, "quantity": 300},
                    {"product_id": p2, "quantity": 500},
                ],
            },
        )
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == 2
        # Entries returned in processed order
        entry_map = {e["product_id"]: e for e in entries}
        assert entry_map[p1]["quantity_delta"] == -300
        assert entry_map[p1]["balance_after"] == 700
        assert entry_map[p1]["movement_type"] == "sale_pos"
        assert entry_map[p1]["created_at"].endswith("Z")
        assert entry_map[p2]["quantity_delta"] == -500
        assert entry_map[p2]["balance_after"] == 1500

        # Verify current stock on products
        assert client.get(f"/api/v1/products/{p1}").json()["current_stock"] == 700
        assert client.get(f"/api/v1/products/{p2}").json()["current_stock"] == 1500

    def test_pos_batch_sale_atomic_rollback_on_insufficient_stock(
        self, client: TestClient
    ):
        p1 = create_test_product(client, sku="BATCH-ROLLBACK-1", current_stock=1000)
        p2 = create_test_product(client, sku="BATCH-ROLLBACK-2", current_stock=200)

        # p1 has enough stock (1000 >= 300), but p2 has insufficient stock (200 < 500)
        resp = client.post(
            "/api/v1/inventory/sale-pos/batch",
            json={
                "ticket_reference_id": "TICKET-BATCH-FAIL",
                "items": [
                    {"product_id": p1, "quantity": 300},
                    {"product_id": p2, "quantity": 500},
                ],
            },
        )
        assert resp.status_code == 400
        assert "Physical stock depleted" in resp.json()["detail"]

        # Ensure atomicity: neither product should have stock deducted
        assert client.get(f"/api/v1/products/{p1}").json()["current_stock"] == 1000
        assert client.get(f"/api/v1/products/{p2}").json()["current_stock"] == 200

    def test_pos_batch_sale_aggregates_duplicate_items(self, client: TestClient):
        p1 = create_test_product(client, sku="BATCH-DUP-1", current_stock=1000)

        resp = client.post(
            "/api/v1/inventory/sale-pos/batch",
            json={
                "ticket_reference_id": "TICKET-BATCH-DUP",
                "items": [
                    {"product_id": p1, "quantity": 200},
                    {"product_id": p1, "quantity": 350},
                ],
            },
        )
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == 1
        assert entries[0]["quantity_delta"] == -550
        assert entries[0]["balance_after"] == 450
        assert client.get(f"/api/v1/products/{p1}").json()["current_stock"] == 450
