from .BaseObject import BaseObject
from ..Coord import Coord
from ..helper import *

class Polygon3D(BaseObject):
    def __init__(
            self,
            points: list = None,
            color: tuple[int, int, int, int] = (0, 0, 0, 255)
    ) -> None:

        super().__init__()

        self.points = points if points is not None else []
        self.color = color
        self._build()

    def _build(self):
        self._empty()

        points = self.points
        color = self.color

        n = len(points)
        if n <= 1: return

        all_y = {p[1] for p in points}
        ys = min(all_y)
        yx = max(all_y)

        lines_x = {}
        lines_z = {}

        for i in range(n):
            x1, y1, z1 = round(Coord(*points[i]))
            x2, y2, z2 = round(Coord(*points[i+1 if i < n-1 else 0]))
            
            if y2 < y1:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
                z1, z2 = z2, z1

            x12 = interpolate(y1, x1, y2, x2)[:-1]
            z12 = interpolate(y1, z1, y2, z2, round=False)[:-1]
            for y in range(y1, y2):
                if y not in lines_x.keys():
                    lines_x[y] = list()
                if y not in lines_z.keys():
                    lines_z[y] = list()

                lines_x[y].append(x12[y - y1])
                lines_z[y].append(z12[y - y1])

        for y in lines_x.keys():
            all_x = lines_x[y]
            all_z = lines_z[y]

            xs, xx = min(all_x), max(all_x)
            zs, zx = min(all_z), max(all_z)

            parity = -1

            zSegment = interpolate(xs, zs, xx, zx, round=False)
            for x in range(xs, xx + 1):
                z = zSegment[x - xs]    
                if x in all_x and all_x.count(x) % 2 != 0:
                    parity = -parity
                if parity == 1 or x in all_x:
                    self._add([x, y, color, z])

    def add_point(self, point):
        self.points.append(point)
        self._modified = True

    def set_points(self, points):
        self.points = points
        self._modified = True

    def set_point(self, point, index):
        self.points[index] = point
        self._modified = True