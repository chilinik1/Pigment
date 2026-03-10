# Document model — holds canvas size, pixel buffer, and metadata
import numpy as np

class Document:
    def __init__(self, width: int, height: int, name: str = "Untitled"):
        self.width = width
        self.height = height
        self.name = name
        # RGBA pixel buffer — shape (height, width, 4), dtype uint8
        self.pixels = np.full((height, width, 4), 255, dtype=np.uint8)
        self.pixels[:, :, 3] = 255  # fully opaque white canvas
        self.modified = False

    def paint_circle(self, cx: float, cy: float, radius: float,
                     color: tuple, opacity: float = 1.0):
        """
        Paint a soft round brush dab at (cx, cy).
        color: (r, g, b) each 0-255
        opacity: 0.0 - 1.0
        """
        r = int(radius)
        x0 = max(0, int(cx - r - 1))
        x1 = min(self.width,  int(cx + r + 2))
        y0 = max(0, int(cy - r - 1))
        y1 = min(self.height, int(cy + r + 2))

        if x0 >= x1 or y0 >= y1:
            return

        # Build coordinate grids for the affected region
        xs = np.arange(x0, x1, dtype=np.float32)
        ys = np.arange(y0, y1, dtype=np.float32)
        xx, yy = np.meshgrid(xs, ys)

        # Distance from centre, normalised to brush radius
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        # Soft falloff: 1 at centre, 0 at edge
        alpha_mask = np.clip(1.0 - dist / max(radius, 0.5), 0.0, 1.0)
        alpha_mask = alpha_mask ** 0.5  # softer edge
        alpha_mask *= opacity

        # Composite onto existing pixels (painter's algorithm)
        region = self.pixels[y0:y1, x0:x1].astype(np.float32)
        for ch, val in enumerate(color):
            region[:, :, ch] = (
                region[:, :, ch] * (1.0 - alpha_mask) +
                val * alpha_mask
            )
        region[:, :, 3] = 255  # keep fully opaque

        self.pixels[y0:y1, x0:x1] = np.clip(region, 0, 255).astype(np.uint8)
        self.modified = True

    def paint_stroke(self, x0: float, y0: float,
                     x1: float, y1: float,
                     radius: float, color: tuple, opacity: float = 1.0):
        """
        Paint a stroke from (x0,y0) to (x1,y1) by stamping
        overlapping brush dabs along the line.
        """
        dx = x1 - x0
        dy = y1 - y0
        dist = max(1.0, np.sqrt(dx * dx + dy * dy))
        # Spacing between dabs — 25% of radius for smooth strokes
        step = max(1.0, radius * 0.25)
        steps = int(dist / step)
        for i in range(steps + 1):
            t = i / max(steps, 1)
            self.paint_circle(
                x0 + dx * t,
                y0 + dy * t,
                radius, color, opacity
            )

    @property
    def title(self):
        marker = " •" if self.modified else ""
        return f"{self.name}{marker} ({self.width}×{self.height})"
