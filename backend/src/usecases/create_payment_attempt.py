from src.domain.exceptions import OrderNotFound
from src.domain.payment import Payment, PaymentMethod
from src.domain.repositories import OrderRepository, PaymentRepository


class CreatePaymentAttempt:
    """Create a payment attempt for an order and mark it paid (simulated)."""

    def __init__(self, order_repo: OrderRepository, payment_repo: PaymentRepository):
        self._order_repo = order_repo
        self._payment_repo = payment_repo

    async def execute(self, order_id: int, method: PaymentMethod) -> Payment:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFound(f"Order {order_id} not found")

        payment = Payment(order_id=order_id, method=method)
        payment.mark_paid()
        await self._payment_repo.create(payment)
        return payment
