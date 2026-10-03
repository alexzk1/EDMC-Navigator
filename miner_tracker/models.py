from dataclasses import dataclass
import datetime
from typing import Optional

@dataclass
class MiningSpot:
    star_system: str
    body_name: str
    latitude: float
    longitude: float
    spot_number: Optional[int] = None
    mineral_type: Optional[str] = None
    amount: Optional[float] = None
    density: Optional[float] = None
    max_miners: int = 1
    last_visit_time: Optional[datetime.datetime] = None

    def to_dict(self) -> dict:
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
            "last_visit_time": self.last_visit_time.isoformat() if self.last_visit_time else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MiningSpot':
        dt = data.get("last_visit_time")
        if dt and isinstance(dt, str):
            data["last_visit_time"] = datetime.datetime.fromisoformat(dt)
        return cls(**data)
