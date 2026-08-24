from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Item:
    name: str
    price: Decimal
    category: str
    icon: str = "plate"
    stock: int = 0
    id: int | None = None
