from .BaseObject import BaseObject
from ..Coord import Coord
from ..helper import *

class Rectangle(BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            thickness: int = 1,
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.color = color
        self.mode = mode
        self.thickness = clamp(thickness, 0, min(x2 - x1, y2 - y1))
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)

        color = self.color
        mode = self.mode
        thickness = self.thickness

        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        
        if mode == "solid":
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self._add([x, y, color])

        elif mode == "outline":
            for t in range(thickness):
                for x in range(x1 + t, x2 - t + 1):
                    self._add([x, y1 + t, color])
                    self._add([x, y2 - t, color])

                for y in range(y1 + t + 1, y2 - t):
                    self._add([x1 + t, y, color])
                    self._add([x2 - t, y, color])

    def set_points(self, x1, y1, x2, y2):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self._modified = True

    def set_mode(self, mode):
        self.mode = mode
        self._modified = True

    def set_thickness(self, thickness):
        self.thickness = clamp(thickness, 0, min(x2 - x1, y2 - y1))
        self._modified = True

    def __copy__(self):
        return Rectangle(
            *self.p1,
            *self.p2,
            mode = self.mode,
            color = self.color
        )