from fastapi.testclient import TestClient

from tests.inventory.conftest import create_test_product


class TestInventoryReceiving:
    def test_supplier_receiving_replenishes_stock(self, client: TestClient):
        product_id = create_test_product(client)

        resp = client.post(
            "/api/v1/inventory/receive",
            json={
                "product_id": product_id,
                "quantity": 10000,  # +10 kg
                "reference_id": "SUPPLIER-INV-1001",
                "notes": "Reception from organic grower",
            },
        )
        assert resp.status_code == 201
        entry = resp.json()
        assert entry["movement_type"] == "receiving"
        assert entry["quantity_delta"] == 10000
        assert entry["balance_after"] == 10000
        assert entry["reference_id"] == "SUPPLIER-INV-1001"

        # Verify product current stock updated
        prod = client.get(f"/api/v1/products/{product_id}").json()
        assert prod["current_stock"] == 10000
        # Virtual stock: max(0, 10000 - 0 - 500) = 9500
        assert prod["virtual_stock"] == 9500


class TestInventoryShrinkageMerma:
    def test_log_merma_deducts_stock(self, client: TestClient):
        product_id = create_test_product(client, current_stock=2000)

        resp = client.post(
            "/api/v1/inventory/merma",
            json={
                "product_id": product_id,
                "quantity": 150,
                "notes": "Accidental spillage during counter scoop",
            },
        )
        assert resp.status_code == 200
        entry = resp.json()
        assert entry["movement_type"] == "shrinkage_merma"
        assert entry["quantity_delta"] == -150
        assert entry["balance_after"] == 1850

        prod = client.get(f"/api/v1/products/{product_id}").json()
        assert prod["current_stock"] == 1850

    def test_merma_exceeding_stock_fails(self, client: TestClient):
        product_id = create_test_product(client, current_stock=100)

        resp = client.post(
            "/api/v1/inventory/merma",
            json={
                "product_id": product_id,
                "quantity": 500,
                "notes": "Excessive shrinkage",
            },
        )
        assert resp.status_code == 400
        assert "Cannot log merma" in resp.json()["detail"]


class TestInventoryAdjustment:
    def test_manual_adjustment_reconciles_count(self, client: TestClient):
        product_id = create_test_product(client, current_stock=5000)

        # Staff counted 4,850g during audit
        resp = client.post(
            "/api/v1/inventory/adjust",
            json={
                "product_id": product_id,
                "counted_stock": 4850,
                "notes": "Weekly audit balance",
                "reference_id": "AUDIT-WEEK-38",
            },
        )
        assert resp.status_code == 200
        entry = resp.json()
        assert entry["movement_type"] == "manual_adjustment"
        assert entry["quantity_delta"] == -150  # 4850 - 5000
        assert entry["balance_after"] == 4850

        prod = client.get(f"/api/v1/products/{product_id}").json()
        assert prod["current_stock"] == 4850
