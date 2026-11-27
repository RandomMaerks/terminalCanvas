from __future__ import annotations

from .BaseObject import BaseObject
from ..Coord import Coord
from ..helper import *

class Triangle(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            x2: int | float = 0, y2: int | float = 0,
            x3: int | float = 0, y3: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            texture: Texture = None,
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.p3 = Coord(x3, y3)
        self.color = color
        self.texture = texture
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)
        x3, y3 = round(self.p3)

        color = self.color
        texture = self.texture

        if y2 < y1:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        if y3 < y1:
            x1, x3 = x3, x1
            y1, y3 = y3, y1
        if y3 < y2:
            x2, x3 = x3, x2
            y2, y3 = y3, y2

        x12 = interpolate(y1, x1, y2, x2)
        x23 = interpolate(y2, x2, y3, x3)
        x13 = interpolate(y1, x1, y3, x3)

        x12.pop(-1)
        x123 = x12 + x23

        m = len(x123) // 2
        if x13[m] < x123[m]: x_left, x_right = x13, x123
        else: x_left, x_right = x123, x13

        for y in range(y1, y3 + 1):
            i = y - y1
            left = x_left[i]
            right = x_right[i]
            for x in range(left, right + 1):
                if texture is None:
                    self._add([x, y, color])
                else:
                    texture_color = texture.get_color_at(
                        (x - left) / max(right - left, 1),
                        (y - y1) / max(y3 - y1, 1)
                    )
                    self._add([x, y, texture_color])

    def set_points(self, x1, y1, x2, y2, x3, y3):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.p3 = Coord(x3, y3)
        self._modified = True

    def set_texture(self, texture: Texture):
        self.texture = texture
        self._modified = True

    def __copy__(self):
        return Triangle(
            *self.p1,
            *self.p2,
            x3 = self.x3, y3 = self.y3,
            color = self.color
        )