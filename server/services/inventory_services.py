"""Temporary backward-compatibility bridge. Purged in Phase 5."""

from server.modules.inventory.movements import (
    _get_locked_product,
    adjust_stock,
    get_locked_product,
    log_merma,
    receive_stock,
)
from server.modules.inventory.pos_fulfillment import (
    fulfill_order,
    record_pos_batch_sale,
    record_pos_sale,
    release_stock,
    reserve_stock,
)
from server.modules.inventory.queries import (
    audit_product_stock,
    get_ledger_history,
)

__all__ = [
    "_get_locked_product",
    "adjust_stock",
    "audit_product_stock",
    "fulfill_order",
    "get_ledger_history",
    "get_locked_product",
    "log_merma",
    "receive_stock",
    "record_pos_batch_sale",
    "record_pos_sale",
    "release_stock",
    "reserve_stock",
]
