from fastapi.testclient import TestClient


def _create_test_product(client: TestClient, **kwargs) -> int:
    payload = {
        "sku": "NUT-CASHEW",
        "name": "Castañas de Cajú",
        "unit_price": 2500,  # $2,500 whole ARS per 100g
        "bulk_reference_grams": 100,
        "plu_code": "0175",
        "product_type": "bulk",
        "current_stock": 0,
        "min_safety_buffer": 500,
    }
    payload.update(kwargs)
    resp = client.post("/api/v1/products", json=payload)
    assert resp.status_code == 200
    prod_id = client.get("/api/v1/products").json()["data"][-1]["id"]
    return prod_id


class TestInventoryReceiving:
    def test_supplier_receiving_replenishes_stock(self, client: TestClient):
        product_id = _create_test_product(client)

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
        product_id = _create_test_product(client, current_stock=2000)

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
        product_id = _create_test_product(client, current_stock=100)

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
        product_id = _create_test_product(client, current_stock=5000)

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


class TestInventoryReservationsAndFulfillment:
    def test_reserve_and_fulfill_delivery_order(self, client: TestClient):
        # 1,200g stock, 500g buffer -> 700g virtual available
        product_id = _create_test_product(
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
        product_id = _create_test_product(
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


class TestPOSSale:
    def test_pos_sale_deducts_with_physical_priority(self, client: TestClient):
        product_id = _create_test_product(client, current_stock=3000)

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

        prod = client.get(f"/api/v1/products/{product_id}").json()
        assert prod["current_stock"] == 2600


class TestStockAuditAndLedgerViews:
    def test_automated_stock_calculation_and_reconciliation(self, client: TestClient):
        product_id = _create_test_product(client, current_stock=0)

        # 1. Receive 10,000g
        client.post(
            "/api/v1/inventory/receive",
            json={
                "product_id": product_id,
                "quantity": 10000,
                "reference_id": "BATCH-1",
            },
        )
        # 2. Sell 2,000g in store
        client.post(
            "/api/v1/inventory/sale-pos",
            json={
                "product_id": product_id,
                "quantity": 2000,
                "ticket_reference_id": "T-1",
            },
        )
        # 3. Log 100g merma
        client.post(
            "/api/v1/inventory/merma",
            json={
                "product_id": product_id,
                "quantity": 100,
                "notes": "Moisture loss",
            },
        )

        audit_resp = client.get(f"/api/v1/inventory/audit/{product_id}")
        assert audit_resp.status_code == 200
        audit = audit_resp.json()

        # Expected stock = 10000 - 2000 - 100 = 7900
        assert audit["current_stock"] == 7900
        assert audit["ledger_calculated_balance"] == 7900
        assert audit["drift"] == 0
        assert audit["is_reconciled"] is True

        # Query paginated ledger history
        ledger_resp = client.get(f"/api/v1/inventory/ledger?product_id={product_id}")
        assert ledger_resp.status_code == 200
        entries = ledger_resp.json()
        assert len(entries) == 3
        # Most recent first
        assert entries[0]["movement_type"] == "shrinkage_merma"
        assert entries[1]["movement_type"] == "sale_pos"
        assert entries[2]["movement_type"] == "receiving"
