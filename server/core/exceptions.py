from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class VitalcerException(Exception):
    """Base domain exception for all Vitalcer business errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EntityNotFoundError(VitalcerException):
    """Raised when an entity cannot be found (maps to HTTP 404)."""

    def __init__(self, entity: str, identifier: str | int) -> None:
        super().__init__(f"{entity} with ID {identifier} not found")
        self.entity = entity
        self.identifier = identifier


class InsufficientStockError(VitalcerException):
    """Raised when physical stock is insufficient (maps to HTTP 400)."""

    def __init__(
        self, item_name: str, requested: int | float, available: int | float
    ) -> None:
        super().__init__(
            f"Physical stock depleted for '{item_name}': "
            f"requested {requested}, available {available}"
        )
        self.item_name = item_name
        self.requested = requested
        self.available = available


class InsufficientVirtualStockError(VitalcerException):
    """Raised when virtual delivery stock is insufficient (maps to HTTP 400)."""

    def __init__(self, requested: int | float, available: int | float) -> None:
        super().__init__(
            f"Insufficient virtual stock for reservation. "
            f"Available: {available}, Requested: {requested}"
        )
        self.requested = requested
        self.available = available


class InvalidMovementError(VitalcerException):
    """Raised on invalid shrinkage or adjustment rules (maps to HTTP 400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers preserving standard {'detail': str} format."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(
        _: Request, exc: EntityNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_handler(
        _: Request, exc: InsufficientStockError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(InsufficientVirtualStockError)
    async def insufficient_virtual_stock_handler(
        _: Request, exc: InsufficientVirtualStockError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidMovementError)
    async def invalid_movement_handler(
        _: Request, exc: InvalidMovementError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(VitalcerException)
    async def general_domain_handler(
        _: Request, exc: VitalcerException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )
