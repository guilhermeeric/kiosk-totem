from dataclasses import dataclass

from pydantic import BaseModel, Field

from src.domain.cart import Cart, CartItem


class CartItemResponse(BaseModel):
    item_id: int
    quantity: int
    unit_price: str
    total: str

    @classmethod
    def from_domain(cls, cart_item: CartItem) -> "CartItemResponse":
        return cls(
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
            unit_price=str(cart_item.unit_price),
            total=str(cart_item.total()),
        )


class CartResponse(BaseModel):
    id: int | None
    session_id: str
    items: list[CartItemResponse]
    total: str

    @classmethod
    def from_domain(cls, cart: Cart) -> "CartResponse":
        return cls(
            id=cart.id,
            session_id=cart.session_id,
            items=[CartItemResponse.from_domain(ci) for ci in cart.items],
            total=str(cart.total()),
        )


@dataclass(frozen=True)
class CreateCartInput:
    session_id: str


class CreateCartRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=255)

    def to_domain(self) -> CreateCartInput:
        return CreateCartInput(session_id=self.session_id)


@dataclass(frozen=True)
class CartItemInput:
    item_id: int
    quantity: int


class CartItemRequest(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

    def to_domain(self) -> CartItemInput:
        return CartItemInput(item_id=self.item_id, quantity=self.quantity)


@dataclass(frozen=True)
class UpdateQuantityInput:
    quantity: int


class UpdateQuantityRequest(BaseModel):
    quantity: int = Field(ge=0)

    def to_domain(self) -> UpdateQuantityInput:
        return UpdateQuantityInput(quantity=self.quantity)
