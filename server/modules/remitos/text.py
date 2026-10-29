import re
import unicodedata

PACKAGING_NOISE = re.compile(
    r"\b(?:x\s*\d+\s*(?:u(?:n(?:idades?)?)?\.?|gr?(?:s|amos?)?|kg|kilos?|lt?|ml|cc))"
    r"|\b(?:caja|pack|bolsa|display|promo|oferta|sachet|sobre|unidad)\b"
    r"|\b(?:de|el|la|los|las|por|con|sin)\b"
    r"|[()[\]{}\-–—/\\|.,;:!?\"'`x×¡¿]",
    re.IGNORECASE,
)


def normalize_supplier_text(raw: str) -> str:
    """Normalize supplier text for deterministic alias dictionary lookups."""
    text = unicodedata.normalize("NFKD", raw)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    noise = {"promo", "oferta", "liq", "liquidacion", "desc", "descuento", "nuevo"}
    tokens = [t for t in text.split() if t not in noise]
    return " ".join(tokens)


def strip_packaging_noise(text: str) -> str:
    """Remove packaging markers and noise words for catalog product comparison."""
    cleaned = PACKAGING_NOISE.sub(" ", text)
    return re.sub(r"\s+", " ", cleaned).strip().lower()
