from .BaseObject import BaseObject
from ..Coord import Coord

class Point(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.color = color
        self._build()

    def _build(self):
        self._empty()

        x, y = round(self.p1)
        color = self.color
        self._add([x, y, color])

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True

    def __copy__(self):
        return Point(
            *self.p1,
            color = self.color
        )