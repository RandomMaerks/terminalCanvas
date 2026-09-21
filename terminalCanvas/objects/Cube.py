import numpy as np

from .BaseCompoundObject import BaseCompoundObject
from .Triangle3D import Triangle3D
from .Line3D import Line3D
from ..Coord import Coord
from ..helper import *

class Cube(BaseCompoundObject):
    def __init__(
            self,
            x1: int | float, y1: int | float, z1: float,
            length: int | float = 1.0,
            mode: str = "solid",
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1, z1)
        self.length = length
        self.mode = mode
        self.color = color
        self._build()

    def _build(self):
        self._empty()

        p1 = self.p1
        length = self.length
        mode = self.mode
        color = self.color

        faces = [
            ((0, 1, 2, 3), (1, 2, 0), (3, 0, 2)),
            ((5, 4, 7, 6), (5, 4, 6), (7, 6, 4)),
            ((1, 5, 6, 2), (2, 1, 5), (6, 2, 5)),
            ((0, 3, 7, 4), (0, 3, 4), (7, 4, 3)),
            ((2, 6, 7, 3), (2, 6, 3), (7, 3, 6)),
            ((0, 4, 5, 1), (1, 0, 5), (4, 5, 0)),
        ]

        halflen = length / 2
        vertices = np.array([
            [-halflen, -halflen, -halflen],
            [ halflen, -halflen, -halflen],
            [ halflen,  halflen, -halflen],
            [-halflen,  halflen, -halflen],
            [-halflen, -halflen,  halflen],
            [ halflen, -halflen,  halflen],
            [ halflen,  halflen,  halflen],
            [-halflen,  halflen,  halflen],
        ])

        for face, tri1, tri2 in faces:
            if mode == "solid":
                self._add(Triangle3D(
                    *(p1 + vertices[tri1[0]]),
                    *(p1 + vertices[tri1[1]]),
                    *(p1 + vertices[tri1[2]]),
                    color = color,
                    backfaceCulling = True,
                ))

                self._add(Triangle3D(
                    *(p1 + vertices[tri2[0]]),
                    *(p1 + vertices[tri2[1]]),
                    *(p1 + vertices[tri2[2]]),
                    color = color,
                    backfaceCulling = True,
                ))
            
            elif mode == "frame":
                for i in range(4):
                    self._add(Line3D(
                        *(p1 + vertices[face[i]]),
                        *(p1 + vertices[face[i+1 if i+1 < 4 else 0]]),
                        color = color,
                    ))