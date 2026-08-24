import pytest

from src.domain.exceptions import CartNotFound, ItemNotFound, NotFound, OrderNotFound


def test_not_found_is_value_error():
    with pytest.raises(NotFound):
        raise NotFound("not found")


def test_not_found_subclasses_share_the_base():
    assert issubclass(CartNotFound, NotFound)
    assert issubclass(ItemNotFound, NotFound)
    assert issubclass(OrderNotFound, NotFound)


def test_cart_not_found_is_value_error():
    with pytest.raises(CartNotFound):
        raise CartNotFound("Cart sess-1 not found")


def test_item_not_found_is_value_error():
    with pytest.raises(ItemNotFound):
        raise ItemNotFound("Item 42 not found")


def test_order_not_found_is_value_error():
    with pytest.raises(OrderNotFound):
        raise OrderNotFound("Order 7 not found")


def test_exceptions_are_value_errors_for_compat():
    assert issubclass(CartNotFound, ValueError)
    assert issubclass(ItemNotFound, ValueError)
    assert issubclass(OrderNotFound, ValueError)
