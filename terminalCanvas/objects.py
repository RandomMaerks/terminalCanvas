import textwrap
from math import sin, cos, pi, sqrt
from copy import copy

from PIL import Image
import numpy as np

from .fonts import font_5x7
from .helper import *
from .coord import Coord

# -----------------
# Base object class
# -----------------

class BaseObject:
    """
    The base object class for all terminalCanvas's objects.
    Mainly for people who want to make shapes and other graphics that can be used in `TCanvas`.

    To make a child object of `BaseObject`, write: `class <ObjectName>(BaseObject):`.

    There are public and private methods that should not be overridden, except for `_build()`.

    `_build()` is a required method which calculates all the pixels that make up the intended object.
    You must have a `_build()` method for your object and it must have `self._empty()` at the very start.
    While building, you can use `self._add(x, y, color)` to add a pixel to the pixel data. Color can be RGB or RGBA.

    There is also the `_modified` attribute, denoting the necessity to be rebuilt when drawn to the canvas.
    When it is drawn, this attribute changes to `False` and will stay as `False` until an attribute is changed where it is set to `True`.
    Every attribute setter method needs to set `_modified` to `True` at the end, otherwise the changes will not apply.

    You can add more methods like getter or setter methods.

    Public methods:
    - `move(x, y)`: move the object by some x and y pixels
    - `scale(x)`: scale the object up by a factor of integer x
    - `set_color((R, G, B[, A]))`: change the color of the object
    - `collides(other)`: detect collision of self with other
    - `includes((x, y))`: detect coordinate on pixel data of self

    Private methods:
    - `_empty()`: reset pixel data and edges
    - `_add(x, y, (R, G, B[, A]))`: add pixel to pixel data, as well as updating edges
    - `_build()`: recalculate pixel data
    
    Attributes:
    - `data`: a list of pixels, each of which contains coordinate and color data
    - `left`, `right`, `top`, `bottom`: edges of the object
    - `_modified`: state of object, whether its attributes have been modified
    """

    def __init__(self) -> None:
        """
        Initialises `BaseObject`.
        """
        self._modified = False
        self._empty()

    def _empty(self):
        """
        Refreshes pixel data and edges for building.
        """

        self.data = []
        self.left = self.right = self.top = self.bottom = 0

    # Pixel insertion, edge detection

    def _add(self, pixel: list) -> None:
        self.data.append(pixel)

        x, y, *_ = pixel
        if x < self.left: self.left = x
        if x > self.right: self.right = x
        if y < self.top: self.top = y
        if y > self.bottom: self.bottom = y

    # Empty build method

    def _build(self):
        raise NotImplementedError

    # Object transformation

    def move(self, xShift: int, yShift: int) -> None:
        self.data = [
            [x + xShift, y + yShift, color, *_]
            for x, y, color, *_ in self.data
        ]

    def scale(self, amount: int) -> None:
        xAnchor = (self.right - self.left) // 2
        yAnchor = (self.bottom - self.top) // 2
        scaled = []
        for x, y, color, *_ in self.data:
            xShift = (x - xAnchor) * (amount - 1)
            yShift = (y - yAnchor) * (amount - 1)
            for i in range(amount):
                for j in range(amount):
                    scaled.append([x + i + xShift, y + j + yShift, color, *_])
        self.data = scaled

    def set_color(self, color: tuple[int, int, int, int]) -> None:
        self.color = color
        self._modified = True

    # Collision detection

    def collides(self, other) -> bool:
        pixels1 = set((x, y) for x, y, *_ in self.data)
        pixels2 = set((x, y) for x, y, *_ in other.data)

        return not pixels1.isdisjoint(pixels2)

    # Other methods

    def __contains__(self, point: tuple[int, int]) -> bool:
        pixels = set((x, y) for x, y, *_ in self.data)

        return point in pixels

# ----------
# 2D objects
# ----------
    
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
    

class Line(BaseObject):
    """
    Bresenham's line algorithm, with thickness implemented.

    Original implementation from Armin Joachimsmeyer:
    https://github.com/ArminJo/Arduino-BlueDisplay/blob/master/src/LocalGUI/ThickLine.hpp
    """

    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            x2: int | float = 0, y2: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            thickness: int = 1,
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.color = color
        self.thickness = max(0, thickness)
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)

        thickness = self.thickness

        color = self.color

        if thickness <= 1:
            self._drawLineOverlap(x1, y1, x2, y2, color)
        else:
            dy = x2 - x1
            dx = y2 - y1

            swap = True
            if dx < 0:
                dx = -dx
                sx = -1
                swap = not swap
            else:
                sx = 1

            if dy < 0:
                dy = -dy
                sy = -1
                swap = not swap
            else:
                sy = 1

            dx2 = dx << 1
            dy2 = dy << 1

            offset = thickness // 2

            if dx >= dy:
                if swap:
                    offset = (thickness - 1) - offset
                    sy = -sy
                else:
                    sx = -sx
                    
                error = dy2 - dx
                for i in range(offset, 0, -1):
                    x1 -= sx
                    x2 -= sx
                    if error >= 0:
                        y1 -= sy
                        y2 -= sy
                        error -= dx2
                    error += dy2

                self._drawLineOverlap(x1, y1, x2, y2, color)

                error = dy2 - dx
                for i in range(thickness, 1, -1):
                    x1 += sx
                    x2 += sx
                    overlap = "none"
                    if error >= 0:
                        y1 += sy
                        y2 += sy
                        error -= dx2
                        overlap = "major"
                    error += dy2

                    self._drawLineOverlap(x1, y1, x2, y2, color, overlap)
            else:
                if swap:
                    sx = -sx
                else:
                    offset = (thickness - 1) - offset
                    sy = -sy

                error = dx2 - dy
                for i in range(offset, 0, -1):
                    y1 -= sy
                    y2 -= sy
                    if error >= 0:
                        x1 -= sx
                        x2 -= sx
                        error -= dy2
                    error += dx2

                self._drawLineOverlap(x1, y1, x2, y2, color)

                error = dx2 - dy
                for i in range(thickness, 1, -1):
                    y1 += sy
                    y2 += sy
                    overlap = "none"
                    if error >= 0:
                        x1 += sx
                        x2 += sx
                        error -= dy2
                        overlap = "major"
                    error += dx2

                    self._drawLineOverlap(x1, y1, x2, y2, color, overlap)
     
    def _drawLineOverlap(
            self,
            x1: int, y1: int,
            x2: int, y2: int,
            color: tuple[int, int, int, int],
            overlap: str = "none"
    ):
        dx = x2 - x1
        dy = y2 - y1

        if dx < 0:
            dx = -dx
            sx = -1
        else:
            sx = 1

        if dy < 0:
            dy = -dy
            sy = -1
        else:
            sy = 1

        dx2 = dx << 1
        dy2 = dy << 1

        self._add([x1, y1, color])
        if dx > dy:
            error = dy2 - dx
            while x1 != x2:
                x1 += sx
                if error >= 0:
                    if overlap == "major": self._add([x1, y1, color])
                    y1 += sy
                    if overlap == "minor": self._add([x1 - sx, y1, color])
                    error -= dx2
                error += dy2
                self._add([x1, y1, color])
        else:
            error = dx2 - dy
            while y1 != y2:
                y1 += sy
                if error >= 0:
                    if overlap == "major": self._add([x1, y1, color])
                    x1 += sx
                    if overlap == "minor": self._add([x1, y1 - sy, color])
                    error -= dy2
                error += dx2
                self._add([x1, y1, color])        

    def set_points(self, x1, y1, x2, y2):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self._modified = True

    def set_thickness(self, thickness):
        self.thickness = max(0, thickness)
        self._modified = True

    def __copy__(self):
        return Line(
            *self.p1,
            *self.p2,
            color = self.color,
            thickness = self.thickness
        )


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

        
class Triangle(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            x2: int | float = 0, y2: int | float = 0,
            x3: int | float = 0, y3: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255)
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.p3 = Coord(x3, y3)
        self.color = color
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)
        x3, y3 = round(self.p3)

        color = self.color

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
        if x13[m] < x123[m]: xLeft, xRight = x13, x123
        else: xLeft, xRight = x123, x13

        for y in range(y1, y3 + 1):
            i = y - y1
            left = xLeft[i]
            right = xRight[i]
            for x in range(left, right + 1):
                self._add([x, y, color])

    def set_points(self, x1, y1, x2, y2, x3, y3):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.p3 = Coord(x3, y3)
        self._modified = True

    def __copy__(self):
        return Triangle(
            *self.p1,
            *self.p2,
            x3 = self.x3, y3 = self.y3,
            color = self.color
        )

class Rectangle(BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            thickness: int = 1,
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.color = color
        self.mode = mode
        self.thickness = clamp(thickness, 0, min(x2 - x1, y2 - y1))
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)

        color = self.color
        mode = self.mode
        thickness = self.thickness

        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        
        if mode == "solid":
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self._add([x, y, color])

        elif mode == "outline":
            for t in range(thickness):
                for x in range(x1 + t, x2 - t + 1):
                    self._add([x, y1 + t, color])
                    self._add([x, y2 - t, color])

                for y in range(y1 + t + 1, y2 - t):
                    self._add([x1 + t, y, color])
                    self._add([x2 - t, y, color])

    def set_points(self, x1, y1, x2, y2):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self._modified = True

    def set_mode(self, mode):
        self.mode = mode
        self._modified = True

    def set_thickness(self, thickness):
        self.thickness = clamp(thickness, 0, min(x2 - x1, y2 - y1))
        self._modified = True

    def __copy__(self):
        return Rectangle(
            *self.p1,
            *self.p2,
            mode = self.mode,
            color = self.color
        )

class Ellipse(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.color = color
        self.mode = mode
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)

        color = self.color
        mode = self.mode

        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1

        rx = abs(x2 - x1) // 2
        ry = abs(y2 - y1) // 2

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        rx2 = rx * rx
        ry2 = ry * ry

        if mode == "solid":
            if rx2 == 0 or ry2 == 0:
                return

            for y in range(-ry, ry + 1):
                xMax = roundInt(rx * (1 - (y*y)/(ry2))**0.5)

                for x in range(-xMax, xMax+1):
                    self._add([cx + x, cy + y, color])

        elif mode == "outline":
            x = 0
            y = ry

            dx = 2 * ry2 * x
            dy = 2 * rx2 * y

            d1 = ry2 - (rx2 * ry) + (0.25 * rx2)

            while dx < dy:
                self._add([cx + x, cy + y, color])
                self._add([cx - x, cy + y, color])
                self._add([cx + x, cy - y, color])
                self._add([cx - x, cy - y, color])

                if d1 < 0:
                    x += 1
                    dx += 2 * ry2
                    d1 += dx + ry2
                else:
                    x += 1
                    y -= 1
                    dx += 2 * ry2
                    dy -= 2 * rx2
                    d1 += dx - dy + ry2

            d2 = ry2 * (x + 0.5)*(x + 0.5) + rx2 * (y - 1)*(y - 1) - rx2 * ry2

            while y >= 0:
                self._add([cx + x, cy + y, color])
                self._add([cx - x, cy + y, color])
                self._add([cx + x, cy - y, color])
                self._add([cx - x, cy - y, color])

                if d2 > 0:
                    y -= 1
                    dy -= 2 * rx2
                    d2 += rx2 - dy
                else:
                    y -= 1
                    x += 1
                    dx += 2 * ry2
                    dy -= 2 * rx2
                    d2 += dx - dy + rx2

    def set_points(self, x1, y1, x2, y2):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self._modified = True

    def set_mode(self, mode):
        self.mode = mode
        self._modified = True

    def __copy__(self):
        return Ellipse(
            *self.p1,
            *self.p2,
            mode = self.mode,
            color = self.color
        )

class Text(BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            message: str = "",
            font: dict = None, 
            spacing: int = 0,
            anchor_x: str = "left",
            anchor_y: str = "top",
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.message = message
        self.font = font
        self.spacing = spacing
        self.anchor_x, self.anchor_y = anchor_x, anchor_y
        self.color = color
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)

        messages = self.message.split("\n")
        font = self.font
        spacing = self.spacing
        anchor_x, anchor_y = self.anchor_x, self.anchor_y
        color = self.color   

        if font is None:
            font = font_5x7.regular  

        kerningInfo = font.get("kerning", dict())
        next_xInfo = font.get("next_x", dict())
        offset_xInfo = font.get("offset_x", dict())
        offset_yInfo = font.get("offset_y", dict())
        
        xCurrent = x1
        yCurrent = y1
        
        for message in messages:
            textLines = []
            totalWidth = 0
            glyph = []

            for index, char in enumerate(message):
                if char not in font:
                    xCurrent += 4 + spacing
                    totalWidth += 4 + spacing
                    continue

                glyph = font.get(char)
                charWidth = len(glyph[0])
                next_x = next_xInfo.get(char, 0)
                offset_x = offset_xInfo.get(char, 0)
                offset_y = offset_yInfo.get(char, 0)

                kern = kerningInfo.get(f"{message[index-1]}{char}", 0) if index > 0 else 0

                for y, row in enumerate(glyph):
                    line = []
                    for x, data in enumerate(row):
                        line.append([
                            data, 
                            xCurrent + x + kern + offset_x, 
                            yCurrent + y + offset_y,
                            color
                        ])
                    textLines.append(line)

                xCurrent += charWidth + spacing + kern + next_x + offset_x
                totalWidth += charWidth + spacing + kern + next_x + offset_x
            
            xCurrent = x1
            yCurrent += len(glyph)

            if anchor_x == "left": xOff = 0
            elif anchor_x == "center": xOff = -(totalWidth)//2
            elif anchor_x == "right": xOff = -(totalWidth)

            if anchor_y == "top": yOff = 0
            elif anchor_y == "center": yOff = -len(textLines[0])//2
            elif anchor_y == "bottom": yOff = -len(textLines[0])

            for line in textLines:
                for data, x, y, color in line:
                    if data == "1": self._add([x + xOff, y + yOff, color])

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True

    def set_message(self, message):
        self.message = message
        self._modified = True

    def set_font(self, font):
        self.font = font
        self._modified = True

    def set_spacing(self, spacing):
        self.spacing = spacing
        self._modified = True

    def set_anchor_x(self, anchor_x):
        self.anchor_x = anchor_x
        self._modified = True

    def set_anchor_y(self, anchor_y):
        self.anchor_y = anchor_y
        self._modified = True

    def __copy__(self):
        return Text(
            *self.p1,
            message = self.message,
            font = self.font,
            spacing = self.spacing,
            anchor_x = self.anchor_x, anchor_y = self.anchor_y,
            color = self.color
        )


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

# ----------
# 3D objects
# ----------

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

class Line3D(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0,
            x2: int | float = 0, y2: int | float = 0, z2: float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self.color = color
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1, z1 = round(self.p1)
        x2, y2, z2 = round(self.p2)

        color = self.color
     
        dx = abs(x2 - x1)
        sx = 1 if x1 < x2 else -1

        dy = abs(y2 - y1)
        sy = 1 if y1 < y2 else -1

        dz = abs(z2 - z1)
        sz = 1 if z1 < z2 else -1

        dm = max(dx, dy, dz)
        
        ex = ey = ez = dm/2
        for _ in range(int(dm) + 1):
            self._add([x1, y1, color, z1])

            ex -= dx
            if ex < 0:
                ex += dm
                x1 += sx

            ey -= dy
            if ey < 0:
                ey += dm
                y1 += sy
            
            ez -= dz
            if ez < 0:
                ez += dm
                z1 += sz

    def set_points(self, x1, y1, z1, x2, y2, z2):
        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self._build()

    def __copy__(self):
        return Line3D(
            *self.p1,
            *self.p2,
            color = self.color
        )

class Triangle3D(BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0, 
            x2: int | float = 0, y2: int | float = 0, z2: float = 0, 
            x3: int | float = 0, y3: int | float = 0, z3: float = 0, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self.p3 = Coord(x3, y3, z3)
        self.color = color
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1, z1 = round(self.p1)
        x2, y2, z2 = round(self.p2)
        x3, y3, z3 = round(self.p3)

        color = self.color

        if y2 < y1:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            z1, z2 = z2, z1
        if y3 < y1:
            x1, x3 = x3, x1
            y1, y3 = y3, y1
            z1, z3 = z3, z1
        if y3 < y2:
            x2, x3 = x3, x2
            y2, y3 = y3, y2
            z2, z3 = z3, z2

        x12 = interpolate(y1, x1, y2, x2)
        x23 = interpolate(y2, x2, y3, x3)
        x13 = interpolate(y1, x1, y3, x3)

        z12 = interpolate(y1, z1, y2, z2, round=False)
        z23 = interpolate(y2, z2, y3, z3, round=False)
        z13 = interpolate(y1, z1, y3, z3, round=False)

        x12.pop(-1)
        x123 = x12 + x23

        z12.pop(-1)
        z123 = z12 + z23

        m = len(x123) // 2
        if x13[m] < x123[m]:
            xLeft, xRight = x13, x123
            zLeft, zRight = z13, z123
        else:
            xLeft, xRight = x123, x13
            zLeft, zRight = z123, z13

        for y in range(y1, y3 + 1):
            i = y - y1
            left = xLeft[i]
            right = xRight[i]
            zSegment = interpolate(left, zLeft[i], right, zRight[i], round=False)
            for x in range(left, right + 1):
                z = zSegment[x-left]
                self._add([x, y, color, z])

    def set_points(self, x1, y1, z1, x2, y2, z2, x3, y3, z3):
        self.p1 = Coord(x1, y1, z1)
        self.p2 = Coord(x2, y2, z2)
        self.p3 = Coord(x3, y3, z3)
        self._modified = True

    def __copy__(self):
        return Triangle3D(
            *self.p1,
            *self.p2,
            *self.p3,
            color = self.color
        )

# ----------
# UI objects
# ----------

class RectangleUI(BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "frame",
            char: str = "█",
            color: tuple[int, int, int, int] = (255, 255, 255, 255),
            bgcolor: tuple[int, int, int, int] = (0, 0, 0, 0),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self.color = color
        self.bgcolor = bgcolor
        self.mode = mode
        self.char = char
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)
        x2, y2 = round(self.p2)

        color = self.color
        mode = self.mode
        char = self.char
        bgcolor = self.bgcolor

        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        
        if mode == "solid":
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self._add([x, y, color, char])

        elif mode in (
            "frame", "frame_bold", "frame_round", "frame_double",
            "block_out", "block_in", "block_thick", "block_even",
        ):
            if mode == "frame":
                top    = ["┌", "─"]
                right  = ["┐", "│"]
                bottom = ["┘", "─"]
                left   = ["└", "│"]
            if mode == "frame_bold":
                top    = ["┏", "━"]
                right  = ["┓", "┃"]
                bottom = ["┛", "━"]
                left   = ["┗", "┃"]
            if mode == "frame_double":
                top    = ["╔", "═"]
                right  = ["╗", "║"]
                bottom = ["╝", "═"]
                left   = ["╚", "║"]
            elif mode == "frame_round":
                top    = ["╭", "─"]
                right  = ["╮", "│"]
                bottom = ["╯", "─"]
                left   = ["╰", "│"]

            elif mode == "block_out":
                top    = ["▛", "▀"]
                right  = ["▜", "▐"]
                bottom = ["▟", "▄"]
                left   = ["▙", "▌"]
            elif mode == "block_in":
                top    = ["▗", "▄"]
                right  = ["▖", "▌"]
                bottom = ["▘", "▀"]
                left   = ["▝", "▐"]
            elif mode == "block_thick":
                top    = ["█", "█"]
                right  = ["█", "█"]
                bottom = ["█", "█"]
                left   = ["█", "█"]
            elif mode == "block_even":
                top    = ["█", "▀"]
                right  = ["█", "█"]
                bottom = ["█", "▄"]
                left   = ["█", "█"]

            for x in range(x1, x2):
                self._add([x, y1, color, top[0] if x==x1 else top[1], bgcolor])
                self._add([x+1, y2, color, bottom[0] if x+1==x2 else bottom[1], bgcolor])
            
            for y in range(y1, y2):
                self._add([x1, y+1, color, left[0] if y+1==y2 else left[1], bgcolor])
                self._add([x2, y, color, right[0] if y==y1 else right[1], bgcolor])

    def set_points(self, x1, y1, x2, y2):
        self.p1 = Coord(x1, y1)
        self.p2 = Coord(x2, y2)
        self._modified = True

    def set_bgcolor(self, bgcolor: tuple[int, int, int, int]):
        self.bgcolor = bgcolor
        self._modified = True

    def set_mode(self, mode):
        self.mode = mode
        self._modified = True

    def set_char(self, char):
        self.char = char
        self._modified = True

    def __copy__(self):
        return RectangleUI(
            *self.p1,
            *self.p2,
            mode = self.mode,
            char = self.char,
            color = self.color,
            bgcolor = self.bgcolor
        )

class TextUI(BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            message: str = "",
            anchor_x: str = "left",
            max_width: int = None,
            max_height: int = None,
            cutoff: str = "whole",
            color: tuple[int, int, int, int] = (255, 255, 255, 255),
            bgcolor: tuple[int, int, int, int] = (0, 0, 0, 0),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.message = message
        self.anchor_x = anchor_x
        self.color = color
        self.bgcolor = bgcolor
        self.max_width = max_width
        self.max_height = max_height
        self.cutoff = cutoff
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)

        messages = self.message.split("\n")
        anchor_x = self.anchor_x
        color = self.color
        bgcolor = self.bgcolor
        max_width = self.max_width
        max_height = self.max_height
        cutoff = self.cutoff

        if max_width is not None:
            if max_width <= 0:
                raise ValueError("max_width must be a positive integer.")

            sepmessages = []

            for message in messages:
                message_length = len(message)

                if message_length < max_width:
                    sepmessages.append(message)
                    continue

                if cutoff == "naive":
                    separated = [message[x:x+max_width] for x in range(0, len(message), max_width)]

                    for x in separated:
                        sepmessages.append(x)

                elif cutoff == "whole":
                    newtext = textwrap.wrap(
                        message,
                        width = max(1, max_width)
                    )
                    for text in newtext:
                        sepmessages.append(text)
                            
            if max_height is not None and len(sepmessages) > max_height:
                messages = sepmessages[:max_height+1]
            else:
                messages = sepmessages
        
        y = 0
        for message in messages:
            totalWidth = len(message)

            if anchor_x == "left": xOff = 0
            elif anchor_x == "center": xOff = -(totalWidth)//2
            elif anchor_x == "right": xOff = -(totalWidth)

            for x, char in enumerate(message):
                self._add([x1 + x + xOff, y1 + y, color, char, bgcolor])

            y += 1

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True

    def set_bgcolor(self, bgcolor: tuple[int, int, int, int]):
        self.bgcolor = bgcolor
        self._modified = True

    def set_message(self, message):
        self.message = message
        self._modified = True

    def set_anchor_x(self, anchor_x):
        self.anchor_x = anchor_x
        self._modified = True

    def set_max_width(self, max_width):
        self.max_width = max_width
        self._modified = True

    def set_max_height(self, max_height):
        self.max_height = max_height
        self._modified = True

    def set_cutoff(self, cutoff):
        self.cutoff = cutoff
        self._modified = True

    def __copy__(self):
        return TextUI(
            *self.p1,
            message = self.message,
            anchor_x = self.anchor_x, anchor_y = self.anchor_y,
            max_width = self.max_width, max_height = self.max_height,
            cutoff = self.cutoff,
            color = self.color,
            bgcolor = self.bgcolor
        )

# ---------
# 3D camera
# ---------

class Camera:
    def __init__(
            self,
            width: int, height: int,
            x: float = 0.0, y: float = 0.0, z: float = 0.0,
            ax: float = 0.0, ay: float = 0.0, az: float = 0.0,
            viewportDistance: float = 1.0,
            backfaceCulling: bool = True,
    ) -> None:
        self.width, self.height = width, height

        self.position = np.array([x, y, z])
        self.angle = np.array([ax, ay, az])

        if self.width >= self.height:
            self.hFOV, self.vFOV = self.width / self.height, 1
        else:
            self.hFOV, self.vFOV = 1, self.height / self.width

        self.hRatio = width / self.hFOV
        self.vRatio = height / self.vFOV

        self.viewportDistance = viewportDistance

        sqrt2rec = 1 / sqrt(2)

        nearPlane   = np.array([0.0      , 0.0      , 1.0     ])
        leftPlane   = np.array([sqrt2rec , 0.0      , sqrt2rec])
        rightPlane  = np.array([-sqrt2rec, 0.0      , sqrt2rec])
        bottomPlane = np.array([0.0      , sqrt2rec , sqrt2rec])
        topPlane    = np.array([0.0      , -sqrt2rec, sqrt2rec])

        self.clippingNormals = (nearPlane, leftPlane, rightPlane, bottomPlane, topPlane)
        self.clippingDistances = (self.viewportDistance, 0.0, 0.0, 0.0, 0.0)

        self.backfaceCulling = backfaceCulling

    def draw(
            self,
            object: BaseObject,
            canvas: TCanvas,
            defensive_clipping: bool = False,
    ) -> None:
        width, height = self.width, self.height
        pos = self.position
        ax, ay, az = self.angle
        d = self.viewportDistance
        hR, vR = self.hRatio, self.vRatio
        clippingNormals = self.clippingNormals
        clippingDistances = self.clippingDistances
        wCenter, hCenter = canvas.wCenter, canvas.hCenter

        if object.p1.dim() == 2:
            raise TypeError(f"{type(object)} is not a 3D object, thus cannot be used with Camera.")

        rotMatrix = np.array([
            [cos(ay)*cos(az)                          ,-cos(ay)*sin(az)                          , sin(ay)        ],
            [cos(ax)*sin(az) + sin(ax)*sin(ay)*cos(az), cos(ax)*cos(az) - sin(ax)*sin(ay)*sin(az),-sin(ax)*cos(ay)],
            [sin(ax)*sin(az) - cos(ax)*sin(ay)*cos(az), sin(ax)*cos(az) - cos(ax)*sin(ay)*sin(az), cos(ax)*cos(ay)]
        ])

        has_2p = any(isinstance(object, x) for x in {Line3D, Triangle3D})
        has_3p = any(isinstance(object, x) for x in {Triangle3D})

        # Translate

        points = []

        new_point1 = (object.p1 - pos) @ rotMatrix.T
        points.append(new_point1)

        if has_2p:
            new_point2 = (object.p2 - pos) @ rotMatrix.T
            points.append(new_point2)

        if has_3p:
            new_point3 = (object.p3 - pos) @ rotMatrix.T
            points.append(new_point3)

        # Clip

        # TODO: Properly implement clipping
        for normal, distance in zip(clippingNormals, clippingDistances):
            point_plane_distance = tuple(
                np.dot(normal, point) + distance
                for point in points
            )

            if defensive_clipping and any(d <= 0 for d in point_plane_distance): return
            elif not defensive_clipping and all(d <= 0 for d in point_plane_distance): return

        # Backface culling

        if self.backfaceCulling and has_3p and self._normal(*points) <= 0: return
        
        # Project

        for i, point in enumerate(points):
            z = max(point[2], 0.0005)
            x = (point[0] * d) / z * hR
            y = (point[1] * d) / z * vR

            points[i] = Coord(x, -y, z)

        new_obj = copy(object)
        new_obj.p1 = points[0]
        if has_2p: new_obj.p2 = points[1]
        if has_3p: new_obj.p3 = points[2]

        # Drawing and finalising

        new_obj._modified = True

        temp_xOff, temp_yOff = canvas._xOff, canvas._yOff
        canvas.translate(wCenter, hCenter)
        canvas.draw(new_obj)
        canvas.translate(temp_xOff, temp_yOff)

    def move(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.position += np.array([x, y, z])

    def rotate(self, ax: float = 0.0, ay: float = 0.0, az: float = 0.0) -> None:
        self.angle += np.array([ax, ay, az])

    def detectInput(
            self,
            canvas: TCanvas,
            movementSpeed: float = 0.1,
            rotationSpeed: float = pi/120,
            keymap: dict = None,
    ) -> None:
        yaw = self.angle[1]

        forward = np.array([-sin(yaw), 0, cos(yaw)])
        right = np.array([cos(yaw), 0, sin(yaw)])

        if keymap is None:
            keymap = {
                "forward": "W",
                "backward": "S",
                "left": "A",
                "right": "D",
                "up": "Q",
                "down": "E",

                "lookup": "I",
                "lookdown": "K",
                "turnleft": "J",
                "turnright": "L",
                "counterclockwise": "U",
                "clockwise": "O",
            }
        
        if canvas.keyPressed(keymap["forward"]):
            self.position += forward * movementSpeed
        if canvas.keyPressed(keymap["backward"]):
            self.position -= forward * movementSpeed

        if canvas.keyPressed(keymap["left"]):
            self.position -= right * movementSpeed
        if canvas.keyPressed(keymap["right"]):
            self.position += right * movementSpeed

        if canvas.keyPressed(keymap["up"]):
            self.position[1] += movementSpeed
        if canvas.keyPressed(keymap["down"]):
            self.position[1] -= movementSpeed

        ax = ay = az = 0

        if canvas.keyPressed(keymap["lookup"]):
            ax = rotationSpeed
        if canvas.keyPressed(keymap["lookdown"]):
            ax = -rotationSpeed

        if canvas.keyPressed(keymap["turnleft"]):
            ay = rotationSpeed
        if canvas.keyPressed(keymap["turnright"]):
            ay = -rotationSpeed

        if canvas.keyPressed(keymap["counterclockwise"]):
            az = rotationSpeed
        if canvas.keyPressed(keymap["clockwise"]):
            az = -rotationSpeed

        self.rotate(ax, ay, az)

    def __copy__(self):
        return Camera(
            width = self.width, height = self.height,
            x = self.position[0], y = self.position[1], z = self.position[2],
            ax = self.angle[0], ay = self.angle[1], az = self.angle[2],
            viewportDistance = self.viewportDistance
        )

    def _normal(self, p1, p2, p3) -> float:
        normal = np.cross(p2 - p1, p3 - p1)

        return np.dot(p1, normal)