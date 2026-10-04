from dataclasses import dataclass


@dataclass(slots=True)
class PlayerLocation:
    """Represent the player's transient spatial state."""

    star_system: str
    body_name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    radius: float | None = None
    heading: float | None = None
