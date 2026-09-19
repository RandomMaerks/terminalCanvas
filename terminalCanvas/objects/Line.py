from .BaseObject import BaseObject
from ..Coord import Coord

class Line(BaseObject):
    """
    Bresenham's line algorithm, with thickness implemented.

    Original implementation from Armin Joachimsmeyer:
    https://github.com/ArminJo/Arduino-BlueDisplay/blob/master/src/LocalGUI/ThickLine.hpp
    """

    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            x2: int | float = 0, y2: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            thickness: int = 1,
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.color = color
        self.thickness = max(0, thickness)
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)

        thickness = self.thickness

        color = self.color

        if thickness <= 1:
            self._drawLineOverlap(x1, y1, x2, y2, color)
        else:
            dy = x2 - x1
            dx = y2 - y1

            swap = True
            if dx < 0:
                dx = -dx
                sx = -1
                swap = not swap
            else:
                sx = 1

            if dy < 0:
                dy = -dy
                sy = -1
                swap = not swap
            else:
                sy = 1

            dx2 = dx << 1
            dy2 = dy << 1

            offset = thickness // 2

            if dx >= dy:
                if swap:
                    offset = (thickness - 1) - offset
                    sy = -sy
                else:
                    sx = -sx
                    
                error = dy2 - dx
                for i in range(offset, 0, -1):
                    x1 -= sx
                    x2 -= sx
                    if error >= 0:
                        y1 -= sy
                        y2 -= sy
                        error -= dx2
                    error += dy2

                self._drawLineOverlap(x1, y1, x2, y2, color)

                error = dy2 - dx
                for i in range(thickness, 1, -1):
                    x1 += sx
                    x2 += sx
                    overlap = "none"
                    if error >= 0:
                        y1 += sy
                        y2 += sy
                        error -= dx2
                        overlap = "major"
                    error += dy2

                    self._drawLineOverlap(x1, y1, x2, y2, color, overlap)
            else:
                if swap:
                    sx = -sx
                else:
                    offset = (thickness - 1) - offset
                    sy = -sy

                error = dx2 - dy
                for i in range(offset, 0, -1):
                    y1 -= sy
                    y2 -= sy
                    if error >= 0:
                        x1 -= sx
                        x2 -= sx
                        error -= dy2
                    error += dx2

                self._drawLineOverlap(x1, y1, x2, y2, color)

                error = dx2 - dy
                for i in range(thickness, 1, -1):
                    y1 += sy
                    y2 += sy
                    overlap = "none"
                    if error >= 0:
                        x1 += sx
                        x2 += sx
                        error -= dy2
                        overlap = "major"
                    error += dx2

                    self._drawLineOverlap(x1, y1, x2, y2, color, overlap)
     
    def _drawLineOverlap(
            self,
            x1: int, y1: int,
            x2: int, y2: int,
            color: tuple[int, int, int, int],
            overlap: str = "none"
    ):
        dx = x2 - x1
        dy = y2 - y1

        if dx < 0:
            dx = -dx
            sx = -1
        else:
            sx = 1

        if dy < 0:
            dy = -dy
            sy = -1
        else:
            sy = 1

        dx2 = dx << 1
        dy2 = dy << 1

        self._add([x1, y1, color])
        if dx > dy:
            error = dy2 - dx
            while x1 != x2:
                x1 += sx
                if error >= 0:
                    if overlap == "major": self._add([x1, y1, color])
                    y1 += sy
                    if overlap == "minor": self._add([x1 - sx, y1, color])
                    error -= dx2
                error += dy2
                self._add([x1, y1, color])
        else:
            error = dx2 - dy
            while y1 != y2:
                y1 += sy
                if error >= 0:
                    if overlap == "major": self._add([x1, y1, color])
                    x1 += sx
                    if overlap == "minor": self._add([x1, y1 - sy, color])
                    error -= dy2
                error += dx2
                self._add([x1, y1, color])        

    def set_points(self, x1, y1, x2, y2):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self._modified = True

    def set_thickness(self, thickness):
        self.thickness = max(0, thickness)
        self._modified = True

    def __copy__(self):
        return Line(
            *self.p1,
            *self.p2,
            color = self.color,
            thickness = self.thickness
        )