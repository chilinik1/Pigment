# Document model — holds canvas size, pixel buffer, and metadata
import numpy as np

class Document:
    def __init__(self, width: int, height: int, name: str = "Untitled"):
        self.width = width
        self.height = height
        self.name = name
        # RGBA pixel buffer — shape (height, width, 4), dtype uint8
        # Start with a solid white canvas
        self.pixels = np.full((height, width, 4), 255, dtype=np.uint8)
        # Make alpha channel fully opaque
        self.pixels[:, :, 3] = 255

    @property
    def title(self):
        return f"{self.name} ({self.width}×{self.height})"
