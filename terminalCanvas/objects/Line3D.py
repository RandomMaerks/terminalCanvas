from .BaseObject import BaseObject
from ..Coord import Coord

class Line3D(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0,
            x2: int | float = 0, y2: int | float = 0, z2: float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self.color = color
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1, z1 = round(self.p1)
        x2, y2, z2 = round(self.p2)

        color = self.color
     
        dx = abs(x2 - x1)
        sx = 1 if x1 < x2 else -1

        dy = abs(y2 - y1)
        sy = 1 if y1 < y2 else -1

        dz = abs(z2 - z1)
        sz = 1 if z1 < z2 else -1

        dm = max(dx, dy, dz)
        
        ex = ey = ez = dm/2
        for _ in range(int(dm) + 1):
            self._add([x1, y1, color, z1])

            ex -= dx
            if ex < 0:
                ex += dm
                x1 += sx

            ey -= dy
            if ey < 0:
                ey += dm
                y1 += sy
            
            ez -= dz
            if ez < 0:
                ez += dm
                z1 += sz

    def set_points(self, x1, y1, z1, x2, y2, z2):
        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self._build()

    def __copy__(self):
        return Line3D(
            *self.p1,
            *self.p2,
            color = self.color
        )