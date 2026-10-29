import base64
import io

from PIL import Image, ImageOps

from server.core.exceptions import CorruptImageError

MAX_DIMENSION = 2048
WEBP_QUALITY = 85


def preprocess_image_bytes(raw_bytes: bytes) -> str:
    """Validate image bytes with Pillow, fix EXIF orientation, and encode WebP."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()
        img = Image.open(io.BytesIO(raw_bytes))
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        raise CorruptImageError(
            "Archivo de imagen corrupto o formato no soportado."
        ) from e

    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=WEBP_QUALITY)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{b64}"


def preprocess_image_data_uri(data_uri: str) -> str:
    """Preprocess image data URI: validate corruption, resize, and return WebP."""
    if not data_uri.startswith("data:"):
        raise CorruptImageError("Formato de URI de imagen no válido.")
    try:
        _, b64_data = data_uri.split(",", 1)
        raw_bytes = base64.b64decode(b64_data)
    except Exception as e:
        raise CorruptImageError(
            "Archivo de imagen corrupto o formato no soportado."
        ) from e
    return preprocess_image_bytes(raw_bytes)


def encode_image_bytes(raw_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Encode raw image bytes to base64 data URI (preprocessed via WebP)."""
    try:
        return preprocess_image_bytes(raw_bytes)
    except CorruptImageError:
        b64 = base64.b64encode(raw_bytes).decode("ascii")
        return f"data:{mime_type};base64,{b64}"
