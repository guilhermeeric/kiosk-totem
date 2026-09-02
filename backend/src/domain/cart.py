from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from .item import Item


@dataclass
class CartItem:
    item_id: int
    quantity: int
    unit_price: Decimal

    def total(self) -> Decimal:
        return self.unit_price * Decimal(self.quantity)


@dataclass
class Cart:
    session_id: str
    items: list[CartItem] = field(default_factory=list)
    handed_off_at: datetime | None = None
    coupon_code: str | None = None
    coupon_discount: Decimal = Decimal("0")  # snapshot of coupon value at apply
    id: int | None = None

    # Upper bound keeps per-item totals inside DECIMAL(10,2) for kiosk items.
    MAX_QUANTITY = 99

    def add_item(self, item: Item, quantity: int = 1) -> None:
        """Add an item to the cart. If it already exists, merge quantities."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > self.MAX_QUANTITY:
            raise ValueError(f"Quantity cannot exceed {self.MAX_QUANTITY}")
        if item.id is None:
            raise ValueError("Item must have an id to be added to a cart")

        # Look for existing cart item
        for cart_item in self.items:
            if cart_item.item_id == item.id:
                merged = cart_item.quantity + quantity
                if merged > self.MAX_QUANTITY:
                    raise ValueError(f"Quantity cannot exceed {self.MAX_QUANTITY}")
                cart_item.quantity = merged
                return

        # New item: snapshot the unit price
        self.items.append(CartItem(item_id=item.id, quantity=quantity, unit_price=item.price))

    def remove_item(self, item_id: int) -> None:
        """Remove an item entirely from the cart."""
        self.items = [ci for ci in self.items if ci.item_id != item_id]

    def update_quantity(self, item_id: int, new_quantity: int) -> None:
        """Update quantity of an existing item. Remove if quantity reaches 0."""
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if new_quantity > self.MAX_QUANTITY:
            raise ValueError(f"Quantity cannot exceed {self.MAX_QUANTITY}")

        for cart_item in self.items:
            if cart_item.item_id == item_id:
                if new_quantity == 0:
                    self.remove_item(item_id)
                else:
                    cart_item.quantity = new_quantity
                return

        raise ValueError(f"Item {item_id} not in cart")

    def apply_coupon(self, coupon_code: str, total_discount: Decimal) -> None:
        """Attach a coupon snapshot. Called by Coupon.add after its rules pass;
        re-apply replaces. No validation here — the gate owns it."""
        self.coupon_code = coupon_code
        self.coupon_discount = total_discount

    def remove_coupon(self) -> None:
        self.coupon_code = None
        self.coupon_discount = Decimal("0")

    def subtotal(self) -> Decimal:
        """Sum of line prices (the full-price story)."""
        return sum(ci.total() for ci in self.items)

    def discount(self) -> Decimal:
        """Effective discount: never more than the subtotal (proportional)."""
        subtotal = self.subtotal()
        return self.coupon_discount if self.coupon_discount <= subtotal else subtotal

    def total(self) -> Decimal:
        """Payable total after coupon discount."""
        return self.subtotal() - self.discount()

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def item_count(self) -> int:
        """Total number of individual items (sum of quantities)."""
        return sum(ci.quantity for ci in self.items)
