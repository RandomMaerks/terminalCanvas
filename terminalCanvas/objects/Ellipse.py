from .BaseObject import BaseObject
from ..Coord import Coord
from ..helper import *

class Ellipse(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.color = color
        self.mode = mode
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)

        color = self.color
        mode = self.mode

        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1

        rx = abs(x2 - x1) // 2
        ry = abs(y2 - y1) // 2

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        rx2 = rx * rx
        ry2 = ry * ry

        if mode == "solid":
            if rx2 == 0 or ry2 == 0:
                return

            for y in range(-ry, ry + 1):
                xMax = roundInt(rx * (1 - (y*y)/(ry2))**0.5)

                for x in range(-xMax, xMax+1):
                    self._add([cx + x, cy + y, color])

        elif mode == "outline":
            x = 0
            y = ry

            dx = 2 * ry2 * x
            dy = 2 * rx2 * y

            d1 = ry2 - (rx2 * ry) + (0.25 * rx2)

            while dx < dy:
                self._add([cx + x, cy + y, color])
                self._add([cx - x, cy + y, color])
                self._add([cx + x, cy - y, color])
                self._add([cx - x, cy - y, color])

                if d1 < 0:
                    x += 1
                    dx += 2 * ry2
                    d1 += dx + ry2
                else:
                    x += 1
                    y -= 1
                    dx += 2 * ry2
                    dy -= 2 * rx2
                    d1 += dx - dy + ry2

            d2 = ry2 * (x + 0.5)*(x + 0.5) + rx2 * (y - 1)*(y - 1) - rx2 * ry2

            while y >= 0:
                self._add([cx + x, cy + y, color])
                self._add([cx - x, cy + y, color])
                self._add([cx + x, cy - y, color])
                self._add([cx - x, cy - y, color])

                if d2 > 0:
                    y -= 1
                    dy -= 2 * rx2
                    d2 += rx2 - dy
                else:
                    y -= 1
                    x += 1
                    dx += 2 * ry2
                    dy -= 2 * rx2
                    d2 += dx - dy + rx2

    def set_points(self, x1, y1, x2, y2):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self._modified = True

    def set_mode(self, mode):
        self.mode = mode
        self._modified = True

    def __copy__(self):
        return Ellipse(
            *self.p1,
            *self.p2,
            mode = self.mode,
            color = self.color
        )