import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from server.models.inventory_ledger import InventoryLedger, InventoryMovementType
from server.models.products import Product, ProductType
from server.models.users import User


class TestUserModel:
    def test_create_user(self, db_session: Session):
        user = User(username="carolina", hashed_pass="secrethash")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "carolina"
        assert user.hashed_pass == "secrethash"

        queried = db_session.exec(select(User).where(User.id == user.id)).first()
        assert queried is not None
        assert queried.username == "carolina"


class TestProductModel:
    def test_create_discrete_product(self, db_session: Session):
        cookie = Product(
            sku="COOKIE-OREO-120G",
            name="Galletitas Oreo 120g",
            product_type=ProductType.DISCRETE,
            unit_price=1800,  # 1,800 whole ARS
            current_stock=24,
        )
        db_session.add(cookie)
        db_session.commit()
        db_session.refresh(cookie)

        assert cookie.id is not None
        assert cookie.sku == "COOKIE-OREO-120G"
        assert cookie.product_type == ProductType.DISCRETE
        assert cookie.unit_price == 1800
        assert cookie.bulk_reference_grams == 100
        assert cookie.current_stock == 24
        assert cookie.reserved_stock == 0
        assert cookie.min_safety_buffer == 0
        assert cookie.is_active is True
        assert cookie.sync_pedidosya is True
        assert cookie.sync_rappi is True
        assert cookie.sync_vgo is True
        assert cookie.sync_mercadolibre is False
        assert cookie.created_at is not None
        assert cookie.updated_at is not None

    def test_create_bulk_product(self, db_session: Session):
        almonds = Product(
            sku="NUT-ALMOND-PEL",
            plu_code="0142",
            name="Almendras Peladas Non Pareil",
            product_type=ProductType.BULK,
            unit_price=1500,  # 1,500 whole ARS per 100g
            bulk_reference_grams=100,
            current_stock=15000,  # 15,000 grams = 15 kg
            min_safety_buffer=500,
        )
        db_session.add(almonds)
        db_session.commit()
        db_session.refresh(almonds)

        assert almonds.id is not None
        assert almonds.sku == "NUT-ALMOND-PEL"
        assert almonds.plu_code == "0142"
        assert almonds.product_type == ProductType.BULK
        assert almonds.unit_price == 1500
        assert almonds.bulk_reference_grams == 100
        assert almonds.current_stock == 15000
        assert almonds.min_safety_buffer == 500

    def test_sku_uniqueness_enforced(self, db_session: Session):
        p1 = Product(
            sku="UNIQUE-SKU",
            name="Product 1",
            unit_price=500,
        )
        db_session.add(p1)
        db_session.commit()

        p2 = Product(
            sku="UNIQUE-SKU",
            name="Product 2 with duplicate SKU",
            unit_price=800,
        )
        db_session.add(p2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestInventoryLedgerModel:
    def test_record_movements_and_relationships(self, db_session: Session):
        product = Product(
            sku="CHIA-SEED",
            plu_code="0210",
            name="Semillas de Chía",
            product_type=ProductType.BULK,
            unit_price=800,  # $800 ARS per 100g
            current_stock=0,
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # 1. Supplier receiving (stock replenishment)
        entry_receiving = InventoryLedger(
            product_id=product.id,
            movement_type=InventoryMovementType.SUPPLIER_RECEIVING,
            quantity_delta=10000,  # +10,000 grams
            balance_after=10000,
            reference_id="INV-SUPPLIER-2026-001",
            notes="Receiving from bulk supplier",
        )
        db_session.add(entry_receiving)

        # 2. In-store POS sale
        entry_sale = InventoryLedger(
            product_id=product.id,
            movement_type=InventoryMovementType.SALE_POS,
            quantity_delta=-350,  # -350 grams
            balance_after=9650,
            reference_id="POS-TICKET-0042",
        )
        db_session.add(entry_sale)

        # 3. Shrinkage / Merma
        entry_merma = InventoryLedger(
            product_id=product.id,
            movement_type=InventoryMovementType.SHRINKAGE_MERMA,
            quantity_delta=-50,  # -50 grams spilled
            balance_after=9600,
            notes="Spillage during scoop",
        )
        db_session.add(entry_merma)

        # 4. Delivery fulfilled
        entry_delivery = InventoryLedger(
            product_id=product.id,
            movement_type=InventoryMovementType.DELIVERY_FULFILLED,
            quantity_delta=-500,  # -500 grams dispatched
            balance_after=9100,
            reference_id="PEYA-ORDER-9912",
        )
        db_session.add(entry_delivery)

        # 5. Manual adjustment
        entry_adj = InventoryLedger(
            product_id=product.id,
            movement_type=InventoryMovementType.MANUAL_ADJUSTMENT,
            quantity_delta=-100,
            balance_after=9000,
            notes="Weekly audit correction",
        )
        db_session.add(entry_adj)
        db_session.commit()

        db_session.refresh(product)

        assert len(product.ledger_entries) == 5
        assert [e.movement_type for e in product.ledger_entries] == [
            InventoryMovementType.SUPPLIER_RECEIVING,
            InventoryMovementType.SALE_POS,
            InventoryMovementType.SHRINKAGE_MERMA,
            InventoryMovementType.DELIVERY_FULFILLED,
            InventoryMovementType.MANUAL_ADJUSTMENT,
        ]

        # Verify back-reference to product
        assert entry_receiving.product is not None
        assert entry_receiving.product.name == "Semillas de Chía"
        assert entry_sale.product is not None
        assert entry_sale.product.sku == "CHIA-SEED"
