
from src.domain.item import Item
from src.domain.repositories import ItemRepository


class ListItems:
    def __init__(self, repo: ItemRepository):
        self._repo = repo

    async def execute(self) -> list[Item]:
        return await self._repo.list_all()
