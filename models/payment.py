from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Payment:
    member_id: str
    member_name: str
    payment_date: str
    amount: int
    plan: str
    due_date: str
    grace_period: bool = False
    months: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "member_id": self.member_id,
            "member_name": self.member_name,
            "payment_date": self.payment_date,
            "amount": self.amount,
            "plan": self.plan,
            "due_date": self.due_date,
            "grace_period": self.grace_period,
            "months": self.months,
            "created_at": self.created_at,
        }
        if self._id:
            data["_id"] = self._id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Payment":
        return cls(
            _id=str(data.get("_id")),
            member_id=data.get("member_id", ""),
            member_name=data.get("member_name", ""),
            payment_date=data.get("payment_date", ""),
            amount=data.get("amount", 0),
            plan=data.get("plan", ""),
            due_date=data.get("due_date", ""),
            grace_period=data.get("grace_period", False),
            months=data.get("months", 1),
            created_at=data.get("created_at", datetime.utcnow()),
        )
