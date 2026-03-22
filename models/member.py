from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


@dataclass
class Member:
    name: str
    phone: Optional[str] = None
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "phone": self.phone,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self._id:
            data["_id"] = self._id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Member":
        return cls(
            _id=str(data.get("_id")),
            name=data.get("name", ""),
            phone=data.get("phone"),
            active=data.get("active", True),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
        )
