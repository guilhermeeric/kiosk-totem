from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PaymentMethod(StrEnum):
    PIX = "PIX"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    CASH = "CASH"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


@dataclass
class Payment:
    order_id: int
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def mark_paid(self) -> None:
        if self.status != PaymentStatus.PENDING:
            raise ValueError(f"Payment is already {self.status.value.lower()}")
        self.status = PaymentStatus.PAID

    def mark_failed(self) -> None:
        if self.status != PaymentStatus.PENDING:
            raise ValueError(f"Payment is already {self.status.value.lower()}")
        self.status = PaymentStatus.FAILED
