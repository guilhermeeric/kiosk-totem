from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Item:
    name: str
    price: Decimal
    category: str
    id: int | None = None
