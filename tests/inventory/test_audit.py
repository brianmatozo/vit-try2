from fastapi.testclient import TestClient

from tests.inventory.conftest import create_test_product


class TestStockAuditAndLedgerViews:
    def test_automated_stock_calculation_and_reconciliation(self, client: TestClient):
        product_id = create_test_product(client, current_stock=0)

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
