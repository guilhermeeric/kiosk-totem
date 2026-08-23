from dataclasses import dataclass, field
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
    id: int
    session_id: str
    items: list[CartItem] = field(default_factory=list)

    def add_item(self, item: Item, quantity: int = 1) -> None:
        """Add an item to the cart. If it already exists, merge quantities."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Look for existing cart item
        for cart_item in self.items:
            if cart_item.item_id == item.id:
                cart_item.quantity += quantity
                return

        # New item: snapshot the unit price
        self.items.append(
            CartItem(
                item_id=item.id,
                quantity=quantity,
                unit_price=item.price
            )
        )

    def remove_item(self, item_id: int) -> None:
        """Remove an item entirely from the cart."""
        self.items = [ci for ci in self.items if ci.item_id != item_id]

    def update_quantity(self, item_id: int, new_quantity: int) -> None:
        """Update quantity of an existing item. Remove if quantity reaches 0."""
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")

        for cart_item in self.items:
            if cart_item.item_id == item_id:
                if new_quantity == 0:
                    self.remove_item(item_id)
                else:
                    cart_item.quantity = new_quantity
                return

        raise ValueError(f"Item {item_id} not in cart")

    def total(self) -> Decimal:
        """Compute the total price of all items in the cart."""
        return sum(ci.total() for ci in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def item_count(self) -> int:
        """Total number of individual items (sum of quantities)."""
        return sum(ci.quantity for ci in self.items)
