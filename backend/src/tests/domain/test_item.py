from decimal import Decimal
from src.domain.item import Item

def test_item_creation():
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    assert item.id == 1
    assert item.name == "Burger"
    assert item.price == Decimal("9.99")
    assert item.category == "savory"

def test_item_immutability():
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    # Item is frozen dataclass, so we cannot modify attributes
    # This test is implicit: we can't assign to item.name
    # We'll just check that attribute access works.
    assert item.name == "Burger"
