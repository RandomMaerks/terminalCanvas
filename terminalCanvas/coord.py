import numpy as np

from .helper import *

class Coord:
    """
    The coordinate class for all terminalCanvas's objects.
    """

    def __init__(
            self,
            x: int | float,
            y: int | float,
            z: int | float | None = None
    ) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self):
        if self.z is None:
            for a in (self.x, self.y):
                yield a
        else:
            for a in (self.x, self.y, self.z):
                yield a

    # Dimension

    def dim(self):
        return self.__len__()

    def __len__(self):
        return 2 if self.z is None else 3

    # Math operations

    def __add__(self, other):
        if isinstance(other, np.ndarray):
            return np.array([
                self.x + other[0],
                self.y + other[1],
                None if self.z is None and len(other) <= 2 else self.z + other[2]
            ])

        return Coord(
            self.x + other.x,
            self.y + other.y,
            None if self.z is None and other.z is None else self.z + other.z
        )

    def __sub__(self, other):
        if isinstance(other, np.ndarray):
            return np.array([
                self.x - other[0],
                self.y - other[1],
                None if self.z is None and len(other) <= 2 else self.z - other[2]
            ])

        return Coord(
            self.x - other.x,
            self.y - other.y,
            None if self.z is None and other.z is None else self.z - other.z
        )

    def __neg__(self):
        return Coord(
            -self.x,
            -self.y,
            None if self.z is None else -self.z
        )

    def __round__(self):
        return Coord(roundInt(self.x), roundInt(self.y), self.z)

    # Comparisons

    def __eq__(self, other):
        if self.z is None or other.z is None:
            return self.x == other.x and self.y == other.y
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __lt__(self, other):
        if self.z is None or other.z is None:
            return self.x < other.x and self.y < other.y
        return self.x < other.x and self.y < other.y and self.z < other.z

    def __gt__(self, other):
        if self.z is None or other.z is None:
            return self.x > other.x and self.y > other.y
        return self.x > other.x and self.y > other.y and self.z > other.z

    def __le__(self, other):
        if self.z is None or other.z is None:
            return self.x <= other.x and self.y <= other.y
        return self.x <= other.x and self.y <= other.y and self.z <= other.z

    def __gt__(self, other):
        if self.z is None or other.z is None:
            return self.x >= other.x and self.y >= other.y
        return self.x >= other.x and self.y >= other.y and self.z >= other.z

    def __repr__(self):
        if self.z is None:
            return f"({self.x}, {self.y})"
        return f"({self.x}, {self.y}, {self.z})"

    def __copy__(self):
        return Coord(x = self.x, y = self.y, z = self.z)