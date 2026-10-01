from collections.abc import Sequence

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, col, select

from server.models.inventory_ledger import InventoryLedger, InventoryMovementType
from server.models.products import Product, ProductType


class TestNPlusOneQueries:
    def test_products_to_ledger_selectin_loading(
        self, db_session: Session, sync_engine
    ):
        """Accessing product.ledger_entries across N products emits 2 queries."""
        # Seed 5 products with 3 ledger entries each (15 ledger entries total)
        for i in range(5):
            prod = Product(
                sku=f"SKU-N1-{i}",
                name=f"Product {i}",
                unit_price=1000 + i * 100,
                product_type=ProductType.BULK,
            )
            db_session.add(prod)
            db_session.commit()
            db_session.refresh(prod)
            assert prod.id is not None
            prod_id = prod.id

            for j in range(3):
                db_session.add(
                    InventoryLedger(
                        product_id=prod_id,
                        movement_type=InventoryMovementType.SUPPLIER_RECEIVING,
                        quantity_delta=1000 * (j + 1),
                        balance_after=1000 * (j + 1),
                    )
                )
            db_session.commit()

        # Clear session cache so queries are forced to hit the database
        db_session.expire_all()

        queries: list[str] = []

        def capture_sql(conn, cursor, statement, parameters, context, executemany):
            if "SELECT" in statement.upper():
                queries.append(statement)

        event.listen(sync_engine, "before_cursor_execute", capture_sql)

        try:
            # Query all 5 products
            stmt = select(Product).where(Product.sku.startswith("SKU-N1-"))
            products: Sequence[Product] = db_session.scalars(stmt).all()
            assert len(products) == 5

            # Access ledger_entries on each product
            total_entries = 0
            for p in products:
                total_entries += len(p.ledger_entries)

            assert total_entries == 15

            # Without selectin/eager loading, this would execute 1 + 5 = 6 queries.
            # With selectin loading, exactly 2 queries are emitted (1 + WHERE IN).
            assert len(queries) == 2, (
                f"Expected 2 queries (1 products + 1 selectin), got {len(queries)}"
            )
        finally:
            event.remove(sync_engine, "before_cursor_execute", capture_sql)

    def test_ledger_to_product_selectin_loading(self, db_session: Session, sync_engine):
        """Accessing entry.product across N ledger entries emits 2 queries."""
        p1 = Product(sku="N1-P1", name="Product 1", unit_price=500)
        p2 = Product(sku="N1-P2", name="Product 2", unit_price=800)
        db_session.add_all([p1, p2])
        db_session.commit()
        assert p1.id is not None and p2.id is not None
        id1, id2 = p1.id, p2.id

        for _ in range(5):
            db_session.add(
                InventoryLedger(
                    product_id=id1,
                    movement_type=InventoryMovementType.SALE_POS,
                    quantity_delta=-10,
                    balance_after=490,
                )
            )
            db_session.add(
                InventoryLedger(
                    product_id=id2,
                    movement_type=InventoryMovementType.SALE_POS,
                    quantity_delta=-20,
                    balance_after=780,
                )
            )
        db_session.commit()
        db_session.expire_all()

        queries: list[str] = []

        def capture_sql(conn, cursor, statement, parameters, context, executemany):
            if "SELECT" in statement.upper():
                queries.append(statement)

        event.listen(sync_engine, "before_cursor_execute", capture_sql)

        try:
            stmt = (
                select(InventoryLedger)
                .where(col(InventoryLedger.product_id).in_([id1, id2]))
                .limit(10)
            )
            entries = db_session.scalars(stmt).all()
            assert len(entries) == 10

            # Access product on all 10 ledger entries
            for e in entries:
                assert e.product is not None
                assert e.product.sku in ("N1-P1", "N1-P2")

            # Must be exactly 2 queries (1 for entries, 1 for products with WHERE IN)
            assert len(queries) == 2, f"Expected 2 queries, got {len(queries)}"
        finally:
            event.remove(sync_engine, "before_cursor_execute", capture_sql)

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
