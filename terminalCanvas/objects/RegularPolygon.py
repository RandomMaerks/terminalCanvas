from math import sin, cos, pi

from .BaseObject import BaseObject
from ..Coord import Coord
from .Polygon import Polygon
from ..helper import *

class RegularPolygon(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            radius: int | float = 10,
            sides: int = 3,
            indent: float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255)
    ):
        
        super().__init__()

        self.p1 = Coord(x1, y1)
        self.radius = radius
        self.color = color
        self.sides = clamp(sides, 1, 360)
        self.indent = indent

        self._build()

    def _build(self):
        self._empty()

        x1, y1 = round(self.p1)
        radius = self.radius
        color = self.color
        sides = self.sides
        indent = self.indent

        angle = 360 / sides

        square = Polygon(
            [
                (
                    radius * (1 - indent * (j % 2)) * sin(i / 180 * pi) + x1,
                    radius * (1 - indent * (j % 2)) * cos(i / 180 * pi) + y1
                )
                for j, i in enumerate(range_float(-180, 180, angle))
            ],
            color = color,
        )

        for pixel in square.data:
            self._add(pixel)

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True
    
    def set_sides(self, sides):
        self.sides = clamp(sides, 1, 360)
        self._modified = True

    def set_indent(self, indent):
        self.indent = indent
        self._modified = True