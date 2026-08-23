from decimal import Decimal

from pydantic import BaseModel, field_validator

from src.domain.item import Item


class ItemResponse(BaseModel):
    id: int
    name: str
    price: str
    category: str

    @field_validator("price", mode="before")
    @classmethod
    def decimal_to_str(cls, v: Decimal | str) -> str:
        return str(v) if isinstance(v, Decimal) else v

    @classmethod
    def from_domain(cls, item: Item) -> "ItemResponse":
        return cls(
            id=item.id,
            name=item.name,
            price=item.price,
            category=item.category,
        )
