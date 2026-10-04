import datetime
from dataclasses import dataclass
from typing import Any


@dataclass
class MiningSpot:
    id: int | None = None
    star_system: str = ""
    body_name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    spot_number: int | None = None
    mineral_type: str | None = None
    amount: float | None = None
    density: float | None = None
    max_miners: int = 1
    last_visit_time: datetime.datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "star_system": self.star_system,
            "body_name": self.body_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "spot_number": self.spot_number,
            "mineral_type": self.mineral_type,
            "amount": self.amount,
            "density": self.density,
            "max_miners": self.max_miners,
            "last_visit_time": self.last_visit_time.isoformat()
            if self.last_visit_time
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MiningSpot":
        dt = data.get("last_visit_time")
        if dt and isinstance(dt, str):
            data["last_visit_time"] = datetime.datetime.fromisoformat(dt)
        return cls(**data)
