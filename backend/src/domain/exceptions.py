class NotFound(ValueError):
    """Base for domain not-found errors; the HTTP layer maps this family to 404."""


class CartNotFound(NotFound):
    """Raised when a cart cannot be found for a session."""


class ItemNotFound(NotFound):
    """Raised when an item cannot be found in the catalog."""


class OrderNotFound(NotFound):
    """Raised when an order cannot be found."""
