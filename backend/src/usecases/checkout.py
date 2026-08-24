from src.domain.exceptions import CartNotFound
from src.domain.order import Order, OrderItem, OrderType
from src.domain.payment import PaymentMethod, PaymentStatus
from src.domain.repositories import (
    CartRepository,
    ItemRepository,
    OrderRepository,
    PaymentRepository,
)
from src.usecases.create_payment_attempt import CreatePaymentAttempt


class Checkout:
    """Convert a cart into an order with its payment attempt, atomically.

    The order, its (simulated) payment, and the stock decrement happen inside
    the same transaction: an order only ever exists once it has been paid, and
    stock can never be oversold.
    """

    def __init__(
        self,
        cart_repo: CartRepository,
        item_repo: ItemRepository,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
    ):
        self._cart_repo = cart_repo
        self._item_repo = item_repo
        self._order_repo = order_repo
        self._payment_repo = payment_repo

    async def execute(
        self,
        session_id: str,
        customer_name: str,
        order_type: OrderType,
        payment_method: PaymentMethod,
        payment_status: PaymentStatus = PaymentStatus.PAID,
    ) -> Order:
        cart = await self._cart_repo.get_by_session_id(session_id)
        if cart is None:
            raise CartNotFound(f"Cart for session {session_id!r} not found")
        if cart.is_empty():
            raise ValueError("Cannot checkout an empty cart")
        if cart.id is None:
            raise ValueError("Cart has no id; cannot be checked out")

        order = Order(
            cart_id=cart.id,
            customer_name=customer_name,
            order_type=order_type,
            items=[
                OrderItem(
                    item_id=ci.item_id,
                    quantity=ci.quantity,
                    unit_price=ci.unit_price,
                )
                for ci in cart.items
            ],
            total=cart.total(),
        )

        # Consume stock before writing anything: on failure nothing is
        # persisted. Lines are processed in item_id order so concurrent
        # checkouts lock item rows consistently (no deadlock).
        for line in sorted(order.items, key=lambda oi: oi.item_id):
            await self._item_repo.consume_stock(line.item_id, line.quantity)

        await self._order_repo.create(order)
        if order.id is None:
            raise ValueError("Order has no id; payment cannot be created")
        payment = await CreatePaymentAttempt(self._order_repo, self._payment_repo).execute(
            order.id, payment_method, payment_status
        )
        order.payments = [payment]
        return order
