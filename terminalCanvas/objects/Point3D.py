from .BaseObject import BaseObject
from ..Coord import Coord

class Point3D(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1, z1)
        self.color = color
        self._build()

    def _build(self):
        self._empty()

        x, y, z = round(self.p1)
        color = self.color
        self._add([x, y, color, z])

    def set_points(self, x1, y1, z1):
        self.p1 = Coord(x1, y1, z1)
        self._modified = True

    def __copy__(self):
        return Point3D(
            *self.p1,
            color = self.color
        )