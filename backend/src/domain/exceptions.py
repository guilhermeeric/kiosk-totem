class CartNotFound(ValueError):
    """Raised when a cart cannot be found for a session."""


class ItemNotFound(ValueError):
    """Raised when an item cannot be found in the catalog."""


class OrderNotFound(ValueError):
    """Raised when an order cannot be found."""
