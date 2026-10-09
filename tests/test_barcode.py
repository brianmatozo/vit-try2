from server.utils.barcode import parse_barcode


class TestBarcodeParser:
    def test_parse_embedded_scale_barcode_12_digits(self):
        # Format: PP(20) IIII(0142) WWWWW(00350) C(7) -> 350 grams of PLU 0142
        result = parse_barcode("200142003507")
        assert result.is_embedded_weight is True
        assert result.sku_or_plu == "0142"
        assert result.weight_grams == 350
        assert result.raw_barcode == "200142003507"

    def test_parse_embedded_scale_barcode_13_digits(self):
        # Real-world label: 20 (prefix) 2126 (PLU) 014400 ($14.400 ARS) 4 (check digit)
        result = parse_barcode("2021260144004")
        assert result.is_embedded_scale is True
        assert result.is_embedded_price is True
        assert result.is_embedded_weight is True
        assert result.sku_or_plu == "2126"
        assert result.embedded_price_whole_ars == 14400
        assert result.weight_grams is None
        assert result.raw_barcode == "2021260144004"

    def test_in_store_prefixes(self):
        for prefix in ["20", "21", "28", "29"]:
            barcode = f"{prefix}99990150000"
            result = parse_barcode(barcode)
            assert result.is_embedded_scale is True
            assert result.is_embedded_price is True
            assert result.is_embedded_weight is True
            assert result.sku_or_plu == "9999"
            assert result.embedded_price_whole_ars == 15000

    def test_parse_discrete_retail_barcode(self):
        # Standard Argentine EAN-13 retail prefix 779...
        result = parse_barcode("7790895000430")
        assert result.is_embedded_weight is False
        assert result.sku_or_plu == "7790895000430"
        assert result.weight_grams is None

    def test_parse_alphanumeric_sku(self):
        result = parse_barcode("COOKIE-OREO-120G")
        assert result.is_embedded_weight is False
        assert result.sku_or_plu == "COOKIE-OREO-120G"
        assert result.weight_grams is None

    def test_whitespace_trimmed(self):
        result = parse_barcode("  200142003507 \n")
        assert result.is_embedded_weight is True
        assert result.sku_or_plu == "0142"
        assert result.weight_grams == 350
