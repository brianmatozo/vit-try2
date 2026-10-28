from server.modules.catalog.models import ProductType
from server.modules.remitos.converter import parse_packaging


def test_parse_packaging_discrete_units():
    res = parse_packaging("Barritas de Chocolate x 12 u (Laddu)")
    assert res.package_type == "caja"
    assert res.multiplier == 12
    assert res.target_unit_type == "discrete_unit"
    assert res.confidence >= 85


def test_parse_packaging_with_inner_weight():
    res = parse_packaging("Barritas de Almendras x 53 gr x 6 u (Vento Fit)")
    assert res.package_type == "caja"
    assert res.multiplier == 6
    assert res.target_unit_type == "discrete_unit"
    assert res.inner_weight_grams == 53


def test_parse_packaging_pack_and_display():
    p1 = parse_packaging("Alfajores pack de 6 unidades")
    assert p1.package_type == "pack"
    assert p1.multiplier == 6

    p2 = parse_packaging("Caramelos display x 24")
    assert p2.package_type == "display"
    assert p2.multiplier == 24


def test_parse_packaging_bulk_kg():
    res = parse_packaging("Almendras Non Pareil x 5 kg", product_type=ProductType.BULK)
    assert res.package_type == "kg"
    assert res.multiplier == 5000
    assert res.target_unit_type == "bulk_grams"


def test_parse_packaging_bulk_bolsa_decimal():
    res = parse_packaging(
        "Almohaditas 3 Sabores x Bolsa 1.5", product_type=ProductType.BULK
    )
    assert res.package_type == "bolsa"
    assert res.multiplier == 1500
    assert res.target_unit_type == "bulk_grams"


def test_parse_packaging_bulk_standalone_kg():
    res = parse_packaging("Caju Tostado x KG", product_type=ProductType.BULK)
    assert res.package_type == "kg"
    assert res.multiplier == 1000
    assert res.target_unit_type == "bulk_grams"


def test_parse_packaging_default_fallback():
    res = parse_packaging("Producto Sin Packaging Especificado")
    assert res.package_type == "unidad"
    assert res.multiplier == 1
    assert res.target_unit_type == "discrete_unit"


def test_parse_all_fixture_descriptions(load_remito_fixture):
    for filename in [
        "natural_output.json",
        "new_day_output.json",
        "vivet_output.json",
    ]:
        data = load_remito_fixture(filename)
        for item in data["items"]:
            desc = item["raw_description"]
            res = parse_packaging(desc)
            assert res.multiplier > 0
            assert res.package_type != ""
