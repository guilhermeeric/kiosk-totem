from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.order import Order, OrderItem, OrderType
from src.domain.payment import Payment, PaymentMethod


class OrderItemResponse(BaseModel):
    item_id: int
    quantity: int
    unit_price: str
    total: str

    @classmethod
    def from_domain(cls, order_item: OrderItem) -> "OrderItemResponse":
        return cls(
            item_id=order_item.item_id,
            quantity=order_item.quantity,
            unit_price=str(order_item.unit_price),
            total=str(order_item.total()),
        )


class PaymentResponse(BaseModel):
    id: int | None
    order_id: int
    method: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_domain(cls, payment: Payment) -> "PaymentResponse":
        return cls(
            id=payment.id,
            order_id=payment.order_id,
            method=payment.method.value,
            status=payment.status.value,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )


class OrderResponse(BaseModel):
    id: int | None
    cart_id: int
    customer_name: str
    order_type: str
    status: str
    total: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    items: list[OrderItemResponse]
    payments: list[PaymentResponse]

    @classmethod
    def from_domain(cls, order: Order) -> "OrderResponse":
        return cls(
            id=order.id,
            cart_id=order.cart_id,
            customer_name=order.customer_name,
            order_type=order.order_type.value,
            status=order.status.value,
            total=str(order.total),
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[OrderItemResponse.from_domain(oi) for oi in order.items],
            payments=[PaymentResponse.from_domain(p) for p in order.payments],
        )


@dataclass(frozen=True)
class CheckoutInput:
    session_id: str
    customer_name: str
    order_type: OrderType


class CheckoutRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=255)
    customer_name: str = Field(min_length=1, max_length=100)
    order_type: OrderType

    def to_domain(self) -> CheckoutInput:
        return CheckoutInput(
            session_id=self.session_id,
            customer_name=self.customer_name,
            order_type=self.order_type,
        )


class CreatePaymentRequest(BaseModel):
    method: PaymentMethod

    def to_domain(self) -> PaymentMethod:
        return self.method
