from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class VitalcerException(Exception):
    """Base domain exception for all Vitalcer business errors."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class EntityNotFoundError(VitalcerException):
    """Raised when an entity cannot be found (maps to HTTP 404)."""

    def __init__(
        self, entity: str, identifier: str | int, code: str = "NOT_FOUND"
    ) -> None:
        super().__init__(f"{entity} with ID {identifier} not found", code=code)
        self.entity = entity
        self.identifier = identifier


class InsufficientStockError(VitalcerException):
    """Raised when physical stock is insufficient (maps to HTTP 400)."""

    def __init__(
        self,
        item_name: str,
        requested: int | float,
        available: int | float,
        code: str = "INSUFFICIENT_STOCK",
    ) -> None:
        super().__init__(
            f"Physical stock depleted for '{item_name}': "
            f"requested {requested}, available {available}",
            code=code,
        )
        self.item_name = item_name
        self.requested = requested
        self.available = available


class InsufficientVirtualStockError(VitalcerException):
    """Raised when virtual delivery stock is insufficient (maps to HTTP 400)."""

    def __init__(
        self,
        requested: int | float,
        available: int | float,
        code: str = "INSUFFICIENT_VIRTUAL_STOCK",
    ) -> None:
        super().__init__(
            f"Insufficient virtual stock for reservation. "
            f"Available: {available}, Requested: {requested}",
            code=code,
        )
        self.requested = requested
        self.available = available


class InvalidMovementError(VitalcerException):
    """Raised on invalid shrinkage or adjustment rules (maps to HTTP 400)."""

    def __init__(self, message: str, code: str = "INVALID_MOVEMENT") -> None:
        super().__init__(message, code=code)


class RemitoConflictError(InvalidMovementError):
    """Raised when remito status conflicts with requested action (maps to HTTP 409)."""

    def __init__(self, message: str, code: str = "REMITO_CONFLICT") -> None:
        super().__init__(message, code=code)


class CorruptImageError(VitalcerException):
    """Raised when an image payload is invalid or unreadable (maps to HTTP 400)."""

    def __init__(
        self,
        message: str = "Archivo de imagen corrupto o formato no soportado.",
        code: str = "CORRUPT_IMAGE",
    ) -> None:
        super().__init__(message, code=code)


class VisionExtractionError(VitalcerException):
    """Raised when vision output is unparseable or malformed (maps to HTTP 422)."""

    def __init__(
        self,
        message: str = "No se pudo interpretar el formato del comprobante.",
        code: str = "VISION_EXTRACTION_ERROR",
    ) -> None:
        super().__init__(message, code=code)


class VisionGatewayError(VitalcerException):
    """Raised when OpenRouter API is unreachable or fails (maps to HTTP 502)."""

    def __init__(
        self,
        message: str = "Error al comunicarse con el servicio de visión OpenRouter.",
        code: str = "VISION_GATEWAY_ERROR",
    ) -> None:
        super().__init__(message, code=code)


class RegisterClosedError(VitalcerException):
    """Raised when a sale is attempted while cash register is closed (HTTP 409)."""

    def __init__(
        self,
        message: str = "No hay una caja abierta. Debe abrir la caja para poder operar.",
        code: str = "REGISTER_CLOSED",
    ) -> None:
        super().__init__(message, code=code)


class ActiveClosureExistsError(VitalcerException):
    """Raised when opening a session while another is active (maps to HTTP 409)."""

    def __init__(
        self,
        message: str = "Ya existe una sesión de caja abierta.",
        code: str = "ACTIVE_CLOSURE_EXISTS",
    ) -> None:
        super().__init__(message, code=code)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers preserving standard {'detail': str}
    along with additive machine-readable 'code'.
    """

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(
        _: Request, exc: EntityNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_handler(
        _: Request, exc: InsufficientStockError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(InsufficientVirtualStockError)
    async def insufficient_virtual_stock_handler(
        _: Request, exc: InsufficientVirtualStockError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(RemitoConflictError)
    async def remito_conflict_handler(
        _: Request, exc: RemitoConflictError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(CorruptImageError)
    async def corrupt_image_handler(_: Request, exc: CorruptImageError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(VisionExtractionError)
    async def vision_extraction_handler(
        _: Request, exc: VisionExtractionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(VisionGatewayError)
    async def vision_gateway_handler(
        _: Request, exc: VisionGatewayError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(RegisterClosedError)
    async def register_closed_handler(
        _: Request, exc: RegisterClosedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(ActiveClosureExistsError)
    async def active_closure_exists_handler(
        _: Request, exc: ActiveClosureExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(InvalidMovementError)
    async def invalid_movement_handler(
        _: Request, exc: InvalidMovementError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(VitalcerException)
    async def general_domain_handler(
        _: Request, exc: VitalcerException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "code": exc.code},
        )
