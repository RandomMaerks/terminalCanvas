from .BaseObject import BaseObject
from ..Coord import Coord
from ..helper import *

class Triangle3D(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0, 
            x2: int | float = 0, y2: int | float = 0, z2: float = 0, 
            x3: int | float = 0, y3: int | float = 0, z3: float = 0, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            backfaceCulling: bool = False
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self.p3 = Coord(x3, y3, z3)
        self.color = color
        self.backfaceCulling = backfaceCulling
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1, z1 = round(self.p1)
        x2, y2, z2 = round(self.p2)
        x3, y3, z3 = round(self.p3)

        color = self.color

        if y2 < y1:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            z1, z2 = z2, z1
        if y3 < y1:
            x1, x3 = x3, x1
            y1, y3 = y3, y1
            z1, z3 = z3, z1
        if y3 < y2:
            x2, x3 = x3, x2
            y2, y3 = y3, y2
            z2, z3 = z3, z2

        x12 = interpolate(y1, x1, y2, x2)
        x23 = interpolate(y2, x2, y3, x3)
        x13 = interpolate(y1, x1, y3, x3)

        z12 = interpolate(y1, z1, y2, z2, round=False)
        z23 = interpolate(y2, z2, y3, z3, round=False)
        z13 = interpolate(y1, z1, y3, z3, round=False)

        x12.pop(-1)
        x123 = x12 + x23

        z12.pop(-1)
        z123 = z12 + z23

        m = len(x123) // 2
        if x13[m] < x123[m]:
            xLeft, xRight = x13, x123
            zLeft, zRight = z13, z123
        else:
            xLeft, xRight = x123, x13
            zLeft, zRight = z123, z13

        for y in range(y1, y3 + 1):
            i = y - y1
            left = xLeft[i]
            right = xRight[i]
            zSegment = interpolate(left, zLeft[i], right, zRight[i], round=False)
            for x in range(left, right + 1):
                z = zSegment[x-left]
                self._add([x, y, color, z])

    def set_points(self, x1, y1, z1, x2, y2, z2, x3, y3, z3):
        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self.p3 = Coord(x3, y3, z3)
        self._modified = True

    def set_backfaceCulling(self, backfaceCulling):
        self.backfaceCulling = backfaceCulling

    def __copy__(self):
        return Triangle3D(
            *self.p1,
            *self.p2,
            *self.p3,
            color = self.color
        )