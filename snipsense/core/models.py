"""Data structures and representations for screen capture operations."""

from dataclasses import dataclass, field
import time
from typing import Optional
from PIL import Image


@dataclass(frozen=True)
class ScreenRegion:
    """Represents a bounded rectangular region on screen in virtual pixel coordinates."""
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Region dimensions must be positive, got width={self.width}, height={self.height}")

    @classmethod
    def from_points(cls, x1: int, y1: int, x2: int, y2: int) -> "ScreenRegion":
        """Constructs a normalized region given any two opposing corner points."""
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return cls(x=left, y=top, width=width, height=height)

    def as_dict(self) -> dict:
        return {"left": self.x, "top": self.y, "width": self.width, "height": self.height}


@dataclass(frozen=True)
class OCRTextBox:
    """Represents a single recognized text block with normalized bounding coordinates."""
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int
    polygon: list[tuple[float, float]]

    def contains_point(self, px: float, py: float) -> bool:
        """Checks if a point (px, py) falls inside this text bounding box."""
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height


@dataclass
class CaptureResult:
    """Represents the output of a completed screen capture action."""
    image: Image.Image
    region: ScreenRegion
    timestamp: float = field(default_factory=time.time)
    window_title: Optional[str] = None
    ocr_boxes: list[OCRTextBox] = field(default_factory=list)
    raw_text: str = ""

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height
