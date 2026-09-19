from PIL import Image
import numpy as np

from .BaseObject import BaseObject
from ..Coord import Coord

class Image(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            image_dir: str = None,
            size: tuple[int, int] | None = None
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.image_dir = image_dir
        self.size = size
        self._build()

    def _build(self):      
        self._empty()
          
        x1, y1 = round(self.p1)

        image_dir = self.image_dir
        size = self.size

        if image_dir is None:
            return 
        
        img = Image.open(image_dir).convert("RGBA")
        if size is not None:
            img = img.resize(size)
        res = np.array(img, dtype=np.uint8)

        for y in range(len(res)):
            for x, color in enumerate(res[y]):
                self._add([x + x1, y + y1, tuple(color)])

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True

    def set_image_dir(self, image_dir):
        self.image_dir = image_dir
        self._modified = True

    def set_size(self, size):
        self.size = size
        self._modified = True

    def __copy__(self):
        return Image(
            *self.p1,
            image_dir = self.image_dir,
            size = self.size
        )