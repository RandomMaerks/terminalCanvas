from .BaseObject import BaseObject
from ..Coord import Coord

class Sprite(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            sprite: list[int | float, int | float, tuple[int, int, int, int]] = None
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.sprite = sprite if sprite is not None else []
        self._build()

    def _build(self):  
        self._empty()
              
        x1, y1 = round(self.p1)

        sprite = self.sprite
        if sprite is None: sprite = []

        xCurrent = x1

        for x, y, color, *_ in sprite:
            self._add([x + x1, y + y1, color])

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True

    def set_sprite(self, sprite):
        self.sprite = sprite
        self._modified = True

    def merge(self, other):
        x1, y1 = self.x1, self.y1
        for x, y, color, *_ in other.data:
            self.sprite.append([x + x1, y + y1, color])
        self._modified = True

    def __copy__(self):
        return Sprite(
            *self.p1,
            sprite = self.sprite
        )