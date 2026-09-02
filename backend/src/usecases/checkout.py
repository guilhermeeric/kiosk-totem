from src.domain.exceptions import CartNotFound
from src.domain.order import Order, OrderItem, OrderType
from src.domain.payment import PaymentMethod, PaymentStatus
from src.domain.repositories import UnitOfWork
from src.usecases.create_payment_attempt import CreatePaymentAttempt


class Checkout:
    """Convert a cart into an order with its payment attempt, atomically.

    The order, its (simulated) payment, and the stock decrement happen inside
    one transaction owned by the unit of work: an order only ever exists once
    it has been paid, and stock can never be oversold.
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def execute(
        self,
        session_id: str,
        customer_name: str,
        order_type: OrderType,
        payment_method: PaymentMethod,
        payment_status: PaymentStatus = PaymentStatus.PAID,
    ) -> Order:
        async with self._uow as uow:
            cart = await uow.carts.get_by_session_id(session_id)
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
                total=cart.subtotal() - cart.discount(),
                coupon_code=cart.coupon_code,
                coupon_discount=cart.discount(),
            )

            # Consume stock before writing anything: on failure nothing is
            # persisted. Lines are processed in item_id order so concurrent
            # checkouts lock item rows consistently (no deadlock).
            for line in sorted(order.items, key=lambda oi: oi.item_id):
                await uow.items.consume_stock(line.item_id, line.quantity)

            await uow.orders.create(order)
            if order.id is None:
                raise ValueError("Order has no id; payment cannot be created")
            payment = await CreatePaymentAttempt(uow.orders, uow.payments).execute(
                order.id, payment_method, payment_status
            )
            # Coupon redemption is a paid-event side effect: consume the use
            # only now, after the payment succeeded, inside this transaction.
            # A failed consume (a concurrent checkout took the last use) rolls
            # back the order, the payment, and the stock — a paid order never
            # coexists with an unconsumed coupon use, and a coupon is never
            # redeemed more times than its quantity.
            if cart.coupon_code is not None:
                await uow.coupons.consume(cart.coupon_code)
            order.payments = [payment]
            return order
