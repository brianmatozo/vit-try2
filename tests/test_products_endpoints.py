from fastapi.testclient import TestClient


def _create_product(client: TestClient, **kwargs) -> dict:
    default_payload = {
        "sku": "ALMOND-PEL-100G",
        "name": "Almendras Peladas",
        "unit_price": 1500,  # $1,500 whole ARS
        "bulk_reference_grams": 100,
        "plu_code": "0142",
        "product_type": "bulk",
        "current_stock": 5000,
        "min_safety_buffer": 500,
    }
    default_payload.update(kwargs)
    resp = client.post("/api/v1/products", json=default_payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestProductFastCRUDEndpoints:
    def test_create_and_get_product(self, client: TestClient):
        _create_product(
            client,
            sku="TEA-GREEN-20U",
            name="Té Verde 20 saquitos",
            unit_price=2200,
            product_type="discrete",
            current_stock=15,
            min_safety_buffer=2,
        )

        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1

        # Fetch by ID
        prod_id = data["data"][0]["id"]
        get_resp = client.get(f"/api/v1/products/{prod_id}")
        assert get_resp.status_code == 200
        prod = get_resp.json()
        assert prod["sku"] == "TEA-GREEN-20U"
        assert prod["unit_price"] == 2200
        assert prod["current_stock"] == 15
        assert prod["min_safety_buffer"] == 2
        # Virtual stock = max(0, 15 - 0 - 2) = 13
        assert prod["virtual_stock"] == 13

    def test_update_product(self, client: TestClient):
        _create_product(
            client,
            sku="BAR-CEREAL",
            name="Barra Cereal",
            unit_price=600,
        )
        prod_id = client.get("/api/v1/products").json()["data"][0]["id"]

        patch_resp = client.patch(
            f"/api/v1/products/{prod_id}",
            json={"unit_price": 750, "name": "Barra Cereal Premium"},
        )
        assert patch_resp.status_code == 200

        updated = client.get(f"/api/v1/products/{prod_id}").json()
        assert updated["unit_price"] == 750
        assert updated["name"] == "Barra Cereal Premium"

    def test_delete_product(self, client: TestClient):
        _create_product(client, sku="TO-DELETE", name="To Delete", unit_price=100)
        prod_id = client.get("/api/v1/products").json()["data"][0]["id"]

        del_resp = client.delete(f"/api/v1/products/{prod_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/api/v1/products/{prod_id}")
        assert get_resp.status_code == 404


class TestBarcodeScannerEndpoint:
    def test_scan_scale_embedded_weight_barcode(self, client: TestClient):
        # Create bulk almonds with PLU 0142 and unit_price 1500 ARS per 100g
        _create_product(
            client,
            sku="NUT-ALMOND",
            plu_code="0142",
            name="Almendras",
            unit_price=1500,
            bulk_reference_grams=100,
            product_type="bulk",
        )

        # Scale prints: 20 (prefix) 0142 (PLU) 00350 (350g) 7 (check digit)
        scan_resp = client.get("/api/v1/products/scan/200142003507")
        assert scan_resp.status_code == 200
        scan_data = scan_resp.json()

        assert scan_data["is_embedded_weight"] is True
        assert scan_data["weight_grams"] == 350
        assert scan_data["product"]["plu_code"] == "0142"
        assert scan_data["product"]["name"] == "Almendras"
        # Subtotal: round((1500 / 100) * 350) = 5250 ARS
        assert scan_data["line_total"] == 5250

    def test_scan_scale_embedded_price_13_digits(self, client: TestClient):
        # Nuez: PLU 2126, $2.880 per 100g, label price $14.400 -> physical weight 500g
        _create_product(
            client,
            sku="2127",
            plu_code="2126",
            name="Nueces x500g extra light",
            unit_price=2880,
            bulk_reference_grams=100,
            product_type="bulk",
        )

        scan_resp = client.get("/api/v1/products/scan/2021260144004")
        assert scan_resp.status_code == 200
        scan_data = scan_resp.json()

        assert scan_data["is_embedded_weight"] is True
        assert scan_data["weight_grams"] == 500
        assert scan_data["line_total"] == 14400
        assert scan_data["product"]["plu_code"] == "2126"
        assert scan_data["product"]["name"] == "Nueces x500g extra light"

    def test_scan_discrete_product(self, client: TestClient):
        _create_product(
            client,
            sku="7791234567890",
            name="Alfajor Vegano",
            unit_price=1800,
            product_type="discrete",
        )

        scan_resp = client.get("/api/v1/products/scan/7791234567890")
        assert scan_resp.status_code == 200
        scan_data = scan_resp.json()

        assert scan_data["is_embedded_weight"] is False
        assert scan_data["weight_grams"] is None
        assert scan_data["line_total"] == 1800
        assert scan_data["product"]["sku"] == "7791234567890"

    def test_scan_unknown_barcode_returns_404(self, client: TestClient):
        resp = client.get("/api/v1/products/scan/UNKNOWN-BARCODE")
        assert resp.status_code == 404

    def test_get_product_by_plu(self, client: TestClient):
        _create_product(
            client,
            sku="WALNUT-HALVES",
            plu_code="0188",
            name="Nueces Mariposa",
            unit_price=2000,
            bulk_reference_grams=100,
            product_type="bulk",
        )

        resp = client.get("/api/v1/products/by-plu/0188")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Nueces Mariposa"

    def test_get_nonexistent_plu_returns_404(self, client: TestClient):
        resp = client.get("/api/v1/products/by-plu/9999")
        assert resp.status_code == 404
