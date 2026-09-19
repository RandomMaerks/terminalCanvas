from .BaseObject import BaseObject
from ..Coord import Coord
from ..helper import *

class Polygon(BaseObject):
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

        lines = {}

        for i in range(n):
            x1, y1 = round(Coord(*points[i]))
            x2, y2 = round(Coord(*points[i+1 if i < n-1 else 0]))
            
            if y2 < y1:
                x1, x2 = x2, x1
                y1, y2 = y2, y1

            x12 = interpolate(y1, x1, y2, x2)[:-1]
            for y in range(y1, y2):
                if y not in lines.keys():
                    lines[y] = list()
                lines[y].append(x12[y - y1])

        for y, all_x in lines.items():
            xs = min(all_x)
            xx = max(all_x)

            parity = -1
            for x in range(xs, xx + 1):
                if x in all_x and all_x.count(x) % 2 != 0:
                    parity = -parity
                if parity == 1 or x in all_x:
                    self._add([x, y, color])

    def add_point(self, point):
        self.points.append(point)
        self._modified = True

    def set_points(self, points):
        self.points = points
        self._modified = True

    def set_point(self, point, index):
        self.points[index] = point
        self._modified = True