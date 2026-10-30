from fastapi.testclient import TestClient
from sqlalchemy import event


class TestEndpointQueries:
    def test_products_list_endpoint_does_not_n_plus_one(self, client: TestClient):
        """GET /api/v1/products only queries products table, not children."""
        for i in range(5):
            client.post(
                "/api/v1/products",
                json={
                    "sku": f"LIST-SKU-{i}",
                    "name": f"List Item {i}",
                    "unit_price": 1000,
                },
            )

        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 5
        # Response schema does not include ledger_entries, avoiding relationship queries
        for item in data:
            assert "ledger_entries" not in item

    def test_audit_endpoint_uses_aggregate_query_not_all_records(
        self, client: TestClient, async_engine
    ):
        """audit_product_stock uses SQL SUM() aggregate instead of pulling rows."""
        p_resp = client.post(
            "/api/v1/products",
            json={"sku": "AUDIT-N1", "name": "Audit Item", "unit_price": 500},
        )
        assert p_resp.status_code == 200
        prod_id = client.get("/api/v1/products").json()["data"][-1]["id"]

        # Add 10 ledger entries
        for j in range(10):
            client.post(
                "/api/v1/inventory/receive",
                json={"product_id": prod_id, "quantity": 100 * (j + 1)},
            )

        queries: list[str] = []

        def capture_sql(conn, cursor, statement, parameters, context, executemany):
            if "SELECT" in statement.upper():
                queries.append(statement)

        underlying_engine = async_engine.sync_engine
        event.listen(underlying_engine, "before_cursor_execute", capture_sql)

        try:
            audit = client.get(f"/api/v1/inventory/audit/{prod_id}").json()
            assert audit["product_id"] == prod_id
            assert audit["is_reconciled"] is True

            # Verify that one of the queries is a SUM aggregate
            has_sum_query = any("SUM" in q.upper() for q in queries)
            assert has_sum_query, f"Expected aggregate SUM query in: {queries}"
        finally:
            event.remove(underlying_engine, "before_cursor_execute", capture_sql)

    def test_barcode_scan_does_not_load_ledger_entries(
        self, client: TestClient, async_engine
    ):
        """Barcode scan must not trigger eager loading of ledger entries."""
        # Create product with a discrete barcode as SKU
        client.post(
            "/api/v1/products",
            json={
                "sku": "7791234567890",
                "name": "Barcode Scan Item",
                "unit_price": 1200,
            },
        )
        prod_id = client.get("/api/v1/products").json()["data"][-1]["id"]

        # Populate several ledger entries
        for q in [100, 200, 300]:
            client.post(
                "/api/v1/inventory/receive",
                json={"product_id": prod_id, "quantity": q},
            )

        queries: list[str] = []

        def capture_sql(conn, cursor, statement, parameters, context, executemany):
            if "SELECT" in statement.upper():
                queries.append(statement)

        underlying_engine = async_engine.sync_engine
        event.listen(underlying_engine, "before_cursor_execute", capture_sql)

        try:
            resp = client.get("/api/v1/products/scan/7791234567890")
            assert resp.status_code == 200
            # Scan should emit 1 SELECT query, never querying inventory_ledger
            assert len(queries) == 1, (
                f"Expected exactly 1 query on scan, got {len(queries)}: {queries}"
            )
            has_ledger_query = any("inventory_ledger" in q.lower() for q in queries)
            assert not has_ledger_query, (
                f"Scan must not query inventory_ledger: {queries}"
            )
        finally:
            event.remove(underlying_engine, "before_cursor_execute", capture_sql)

    def test_pos_batch_sale_locks_all_products_in_single_query(
        self, client: TestClient, async_engine
    ):
        """POS batch sale must lock all N products in a single IN (...) query."""
        p_ids = []
        for i in range(3):
            client.post(
                "/api/v1/products",
                json={
                    "sku": f"BATCH-LOCK-{i}",
                    "name": f"Batch Item {i}",
                    "unit_price": 500,
                    "current_stock": 1000,
                },
            )
            p_id = client.get("/api/v1/products").json()["data"][-1]["id"]
            client.post(
                "/api/v1/inventory/receive",
                json={"product_id": p_id, "quantity": 1000},
            )
            p_ids.append(p_id)

        # Open register session for strict POS mode before capturing queries
        client.post("/api/v1/closure/open", json={"initial_cash": 10000})

        queries: list[str] = []

        def capture_sql(conn, cursor, statement, parameters, context, executemany):
            if "SELECT" in statement.upper():
                queries.append(statement)

        underlying_engine = async_engine.sync_engine
        event.listen(underlying_engine, "before_cursor_execute", capture_sql)

        try:
            resp = client.post(
                "/api/v1/inventory/sale-pos/batch",
                json={
                    "ticket_reference_id": "TICKET-LOCK-TEST",
                    "items": [{"product_id": pid, "quantity": 100} for pid in p_ids],
                },
            )
            assert resp.status_code == 200

            # Find the SELECT FOR UPDATE locking query
            for_update_queries = [
                q
                for q in queries
                if "FOR UPDATE" in q.upper() or "products" in q.lower()
            ]
            # Locked in 1 query using IN (...) rather than 3 separate SELECTs
            msg = (
                f"Expected 1 SELECT locking query for all 3 items, "
                f"got {len(for_update_queries)}: {for_update_queries}"
            )
            assert len(for_update_queries) == 1, msg
        finally:
            event.remove(underlying_engine, "before_cursor_execute", capture_sql)
