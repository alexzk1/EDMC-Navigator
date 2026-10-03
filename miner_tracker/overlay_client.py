import logging
from typing import Optional
try:
    try:
        from EDMCOverlay import edmcoverlay
    except ImportError:
        from edmcoverlay import edmcoverlay
except ImportError:
    edmcoverlay = None

logger = logging.getLogger("MinerTracker")

class OverlayClient:
    """Main class to communicate with binary overlay."""

    def __init__(self, owner: str):
        self.owner = owner
        self._overlay = None 
        if edmcoverlay:
            try:
                # Assuming the library provides an 'Overlay' class or similar as described in README/files
                from edmcoverlay import Overlay # This depends on actual structure, but following user direction
                self._overlay = Overlay()
            except Exception as e:
                logger.error(f"Failed to initialize overlay client: {e}")

    def is_available(self) -> bool:
        return self._overlay is not None

    def send_message(self, msgid: str, text: str, color: str = "white", x: int = 100, y: int = 100, ttl: int = 4):
        if self.is_available():
            try:
                self._overlay.send_message(msgid=msgid, text=text, color=color, x=x, y=y, ttl=ttl)
            except Exception as e:
                logger.error(f"Overlay error sending message: {e}")

    def send_svg(self, svgid: str, svg: str, x: int = 0, y: int = 0):
        if self.is_available():
            try:
                # We provide minimal required arguments to match edmcoverlay's expected API from README/files
                self._overlay.send_svg(svgid=svgid, svg=svg, x=x, y=y)
            except Exception as e:
                logger.error(f"Overlay error sending SVG: {e}")

    def send_shape(self, shapeid: str, shape: str, color: str = "white", fill: str = "transparent", x: int = 0, y: int = 0, w: int = 50, h: int = 50, ttl: int = 4):
        if self.is_available():
            try:
                self._overlay.send_shape(shapeid=shapeid, shape=shape, color=color, fill=fill, x=x, y=y, w=w, h=h, ttl=ttl)
            except Exception as e:
                logger.error(f"Overlay error sending shape: {e}")

