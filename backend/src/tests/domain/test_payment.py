from datetime import datetime

import pytest

from src.domain.payment import Payment, PaymentMethod, PaymentStatus


def test_payment_method_values():
    assert [m.value for m in PaymentMethod] == [
        "PIX",
        "CREDIT_CARD",
        "DEBIT_CARD",
        "CASH",
    ]


def test_payment_starts_pending():
    payment = Payment(order_id=1, method=PaymentMethod.PIX)
    assert payment.order_id == 1
    assert payment.method == PaymentMethod.PIX
    assert payment.status == PaymentStatus.PENDING
    assert payment.id is None


def test_mark_paid_from_pending():
    payment = Payment(order_id=1, method=PaymentMethod.CASH)
    payment.mark_paid()
    assert payment.status == PaymentStatus.PAID


def test_mark_paid_twice_raises():
    payment = Payment(order_id=1, method=PaymentMethod.CASH)
    payment.mark_paid()
    with pytest.raises(ValueError, match="already paid"):
        payment.mark_paid()


def test_mark_failed_from_pending():
    payment = Payment(order_id=1, method=PaymentMethod.PIX)
    payment.mark_failed()
    assert payment.status == PaymentStatus.FAILED


def test_mark_failed_after_paid_raises():
    payment = Payment(order_id=1, method=PaymentMethod.PIX)
    payment.mark_paid()
    with pytest.raises(ValueError, match="paid"):
        payment.mark_failed()


def test_mark_paid_after_failed_raises():
    payment = Payment(order_id=1, method=PaymentMethod.PIX)
    payment.mark_failed()
    with pytest.raises(ValueError, match="failed"):
        payment.mark_paid()


def test_payment_accepts_timestamps():
    created = datetime(2026, 1, 1)
    updated = datetime(2026, 1, 2)
    payment = Payment(
        id=7,
        order_id=1,
        method=PaymentMethod.PIX,
        status=PaymentStatus.PAID,
        created_at=created,
        updated_at=updated,
    )
    assert payment.id == 7
    assert payment.created_at == created
    assert payment.updated_at == updated
