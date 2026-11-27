from math import floor, ceil

from PIL import Image as PILImage
import numpy as np

from ..Coord import Coord
from ..helper import *

class Texture:
    def __init__(
            self,
            texture_dir: str,
            mode: str = "nearest_neighbor",
    ) -> None:
        self.set_texture(texture_dir)
        self.mode = mode

    def get_color_at(self, x: float, y: float) -> tuple[int, int, int, int]:
        """
        x, y in range 0 to 1.
        """

        texture_array = self.texture_array
        mode = self.mode
        
        if mode == "nearest_neighbor":
            return texture_array[
                round((self.height - 1) * y),
                round((self.width - 1) * x)
            ]

        elif mode == "bilinear":
            lerp = self.interpolate_color

            x_pixel = (self.width - 1) * x
            x_floor, x_ceil = floor(x_pixel), ceil(x_pixel)

            y_pixel = (self.height - 1) * y
            y_floor, y_ceil = floor(y_pixel), ceil(y_pixel)
            
            color_y_floor = lerp(
                x_pixel,
                texture_array[y_floor, x_floor],
                texture_array[y_floor, x_ceil],
                x_floor, x_floor + 1,
            )
            color_y_ceil = lerp(
                x_pixel,
                texture_array[y_ceil, x_floor],
                texture_array[y_ceil, x_ceil],
                x_floor, x_floor + 1,
            )

            return lerp(y_pixel, color_y_floor, color_y_ceil, y_floor, y_floor + 1)

    def interpolate_color(
            self,
            value: float,
            color1: tuple[int, int, int, int],
            color2: tuple[int, int, int, int],
            value_min: float = 0,
            value_max: float = 1,
    ) -> tuple[int, int, int, int]:
        return tuple(
            (value_max - value) / (value_max - value_min) * c1 +
            (value - value_min) / (value_max - value_min) * c2
            for c1, c2 in zip(color1, color2)
        )

    def set_texture(self, texture_dir: str) -> None:
        img = PILImage.open(texture_dir).convert("RGBA")
        self.texture_array = np.array(img, dtype=np.uint8)
        self.width, self.height = img.size