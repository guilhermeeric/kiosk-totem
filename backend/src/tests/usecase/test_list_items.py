from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.item import Item
from src.domain.repositories import ItemRepository
from src.usecases.list_items import ListItems


async def test_list_items_returns_items():
    # Create a mock repository that returns a list of items
    mock_repo = AsyncMock(spec=ItemRepository)
    expected_items = [
        Item(id=1, name="Burger", price=Decimal("9.99"), category="savory"),
        Item(id=2, name="Fries", price=Decimal("3.50"), category="savory"),
    ]
    mock_repo.list_all.return_value = expected_items

    use_case = ListItems(mock_repo)
    result = await use_case.execute()

    assert result == expected_items
    mock_repo.list_all.assert_called_once()


async def test_list_items_empty():
    mock_repo = AsyncMock(spec=ItemRepository)
    mock_repo.list_all.return_value = []

    use_case = ListItems(mock_repo)
    result = await use_case.execute()

    assert result == []
    mock_repo.list_all.assert_called_once()


async def test_list_items_repository_error_propagates():
    mock_repo = AsyncMock(spec=ItemRepository)
    mock_repo.list_all.side_effect = Exception("DB error")

    use_case = ListItems(mock_repo)
    with pytest.raises(Exception, match="DB error"):
        await use_case.execute()
