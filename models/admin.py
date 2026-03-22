from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Admin:
    telegram_id: int
    name: str
    role: str = "admin"
    created_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "telegram_id": self.telegram_id,
            "name": self.name,
            "role": self.role,
            "created_at": self.created_at,
        }
        if self._id:
            data["_id"] = self._id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Admin":
        return cls(
            _id=str(data.get("_id")),
            telegram_id=data.get("telegram_id", 0),
            name=data.get("name", ""),
            role=data.get("role", "admin"),
            created_at=data.get("created_at", datetime.utcnow()),
        )
