from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from .payment import Payment


class OrderType(StrEnum):
    EAT_IN = "EAT_IN"
    TAKEAWAY = "TAKEAWAY"


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderItem:
    item_id: int
    quantity: int
    unit_price: Decimal

    def total(self) -> Decimal:
        return self.unit_price * Decimal(self.quantity)


@dataclass
class Order:
    cart_id: int
    customer_name: str
    order_type: OrderType
    items: list[OrderItem]
    total: Decimal
    coupon_code: str | None = None
    coupon_discount: Decimal = Decimal("0")  # discount actually granted at checkout
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime | None = None
    updated_at: datetime | None = None
    payments: list[Payment] = field(default_factory=list)
    id: int | None = None

    def mark_preparing(self) -> None:
        """Transition from PENDING to PREPARING."""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot start preparing an order with status {self.status}")
        self.status = OrderStatus.PREPARING

    def mark_ready(self) -> None:
        """Transition from PREPARING to READY."""
        if self.status != OrderStatus.PREPARING:
            raise ValueError(f"Cannot mark order ready with status {self.status}")
        self.status = OrderStatus.READY

    def mark_completed(self) -> None:
        """Transition from READY to COMPLETED."""
        if self.status != OrderStatus.READY:
            raise ValueError(f"Cannot complete an order with status {self.status}")
        self.status = OrderStatus.COMPLETED

    def cancel(self) -> None:
        """Cancel the order if it hasn't been completed yet."""
        if self.status == OrderStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed order")
        self.status = OrderStatus.CANCELLED
