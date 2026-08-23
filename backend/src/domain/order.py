from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class OrderType(StrEnum):
    EAT_IN = "EAT_IN"
    TAKEAWAY = "TAKEAWAY"

class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

@dataclass
class OrderItem:
    item_id: int
    quantity: int
    unit_price: Decimal

    def total(self) -> Decimal:
        return self.unit_price * Decimal(self.quantity)

@dataclass
class Order:
    id: int
    cart_id: int
    customer_name: str
    order_type: OrderType
    items: list[OrderItem]
    total: Decimal
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime | None = None
    updated_at: datetime | None = None

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

    def mark_paid(self) -> None:
        """Mark payment as successful."""
        if self.payment_status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot change payment status from {self.payment_status}")
        self.payment_status = PaymentStatus.PAID

    def mark_payment_failed(self) -> None:
        """Mark payment as failed."""
        if self.payment_status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot change payment status from {self.payment_status}")
        self.payment_status = PaymentStatus.FAILED
