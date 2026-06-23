from PIL import Image
import numpy as np

from .fonts import font_5x7

# ---------------
# Other functions
# ---------------

def interpolate(i0, d0, i1, d1, round=True):
    if i0 == i1:
        return [roundInt(d0) if round else d0]

    n = i1 - i0
    values = [0] * (n + 1)

    r = roundInt if round else lambda x: x

    delta = (d1 - d0) / n
    d = d0

    for i in range(n + 1):
        values[i] = r(d)
        d += delta

    return values

def roundInt(x):
    try:
        return int(x + 0.5) if x >= 0 else int(x - 0.5)
    except TypeError as e:
        raise TypeError(repr(e) + f" (offender: {x})")

# -----------------
# Base object class
# -----------------

class TC_BaseObject:
    def __init__(self) -> None:
        self.data = []

    # Pixel insertion, early removal

    def add(self, pixel: list) -> None:
        self.data.append(pixel)

    # Empty build method

    def _build(self):
        raise NotImplementedError

    # Object transformation

    def move(self, xShift: int, yShift: int) -> None:
        moved = []
        for x, y, color, *_ in self.data:
            x += xShift
            y += yShift
            moved.append([x, y, color, *_])
        self.data = moved

    def scale(self, amount: int) -> None:
        xTop, yTop, _ = min(self.data)
        scaled = []
        for x, y, color, *_ in self.data:
            for i in range(amount):
                for j in range(amount):
                    xShift = (x-xTop) * (amount-1)
                    yShift = (y-yTop) * (amount-1)
                    scaled.append([x + i + xShift, y + j + yShift, color, *_])
        self.data = scaled

    def set_color(self, color: tuple[int, int, int, int]) -> None:
        self.color = color
        self._build()

# ----------
# 2D objects
# ----------
    
class TC_Point(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.color = color
        self._build()

    def _build(self):
        self.data = []

        x = roundInt(self.x1)
        y = roundInt(self.y1)
        color = self.color
        self.add([x, y, color])

    def set_points(self, x1, y1):
        self.x1, self.y1 = x1, y1
        self._build()
    

class TC_Line(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            x2: int | float = 0, y2: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            antialiasing: bool = False
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
        self.antialiasing = antialiasing
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

        x2 = roundInt(self.x2)
        y2 = roundInt(self.y2)

        color = self.color
     
        dx = abs(x2 - x1)
        sx = 1 if x1 < x2 else -1

        dy = -abs(y2 - y1)
        sy = 1 if y1 < y2 else -1

        error = dx + dy

        if not self.antialiasing:            
            while True:
                self.add([x1, y1, color])

                if x1 == x2 and y1 == y2: break

                e2 = 2 * error

                if e2 >= dy:
                    error += dy
                    x1 += sx
                if e2 <= dx:
                    error += dx
                    y1 += sy
        
        else:
            dy = -dy

            ed = 1 if dx + dy == 0 else (dx*dx + dy*dy) ** 0.5
            r, g, b, *_ = color
            while True:
                aa = 255 - (255 * abs(error - dx + dy) / ed)
                self.add([x1, y1, (r, g, b, aa)])

                e2 = error
                x3 = x1

                if e2 * 2 >= -dx:
                    if x1 == x2: break
                    if e2 + dy < ed:
                        aa = 255 - (255 * (e2 + dy) / ed)
                        self.add([x1, y1 + sy, (r, g, b, aa)])
                    error -= dy
                    x1 += sx

                if e2 * 2 <= dy:
                    if y1 == y2: break
                    if dx - e2 < ed:
                        aa = 255 - (255 * abs(dx - e2) / ed)
                        self.add([x3 + sx, y1, (r, g, b, aa)])
                    error += dx
                    y1 += sy

    def set_points(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self._build()

class TC_Triangle(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            x2: int | float = 0, y2: int | float = 0,
            x3: int | float = 0, y3: int | float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.x3, self.y3 = x3, y3
        self.color = color
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)
        
        x2 = roundInt(self.x2)
        y2 = roundInt(self.y2)
    
        x3 = roundInt(self.x3)
        y3 = roundInt(self.y3)

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
                self.add([x, y, color])

    def set_points(self, x1, y1, x2, y2, x3, y3):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.x3, self.y3 = x3, y3
        self._build()

class TC_Rectangle(TC_BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
        self.mode = mode
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

        x2 = roundInt(self.x2)
        y2 = roundInt(self.y2)

        color = self.color
        mode = self.mode

        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        
        if mode == "solid":
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self.add([x, y, color])

        elif mode == "outline":
            for x in range(x1, x2 + 1):
                self.add([x, y1, color])
                self.add([x, y2, color])

            for y in range(y1 + 1, y2):
                self.add([x1, y, color])
                self.add([x2, y, color])

    def set_points(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self._build()

    def set_mode(self, mode):
        self.mode = mode
        self._build()

class TC_Ellipse(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
        self.mode = mode
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

        x2 = roundInt(self.x2)
        y2 = roundInt(self.y2)

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
                    self.add([cx + x, cy + y, color])

        elif mode == "outline":
            x = 0
            y = ry

            dx = 2 * ry2 * x
            dy = 2 * rx2 * y

            d1 = ry2 - (rx2 * ry) + (0.25 * rx2)

            while dx < dy:
                self.add([cx + x, cy + y, color])
                self.add([cx - x, cy + y, color])
                self.add([cx + x, cy - y, color])
                self.add([cx - x, cy - y, color])

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
                self.add([cx + x, cy + y, color])
                self.add([cx - x, cy + y, color])
                self.add([cx + x, cy - y, color])
                self.add([cx - x, cy - y, color])

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
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self._build()

    def set_mode(self, mode):
        self.mode = mode
        self._build()

class TC_Text(TC_BaseObject):
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

        self.x1, self.y1 = x1, y1
        self.message = message
        self.font = font
        self.spacing = spacing
        self.anchor_x, self.anchor_y = anchor_x, anchor_y
        self.color = color
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

        messages = self.message.split("\n")
        font = self.font
        spacing = self.spacing
        anchor_x, anchor_y = self.anchor_x, self.anchor_y
        color = self.color   

        if font is None:
            font = font_5x7.regular  

        kerningInfo = font.get("kerning")
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

                if index > 0 and kerningInfo is not None:
                    kern = kerningInfo.get(f"{message[index-1]}{char}", 0)
                else:
                    kern = 0

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
                    if data == "1": self.add([x + xOff, y + yOff, color])

    def set_points(self, x1, y1):
        self.x1, self.y1 = x1, y1
        self._build()

    def set_message(self, message):
        self.message = message
        self._build()

    def set_font(self, font):
        self.font = font
        self._build()

    def set_spacing(self, spacing):
        self.spacing = spacing
        self._build()

    def set_anchor_x(self, anchor_x):
        self.anchor_x = anchor_x
        self._build()

    def set_anchor_y(self, anchor_y):
        self.anchor_y = anchor_y
        self._build()


class TC_Image(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            image_dir: str = None,
            size: tuple[int, int] | None = None
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.image_dir = image_dir
        self.size = size
        self._build()

    def _build(self):      
        self.data = []
          
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

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
                self.add([x + x1, y + y1, tuple(color)])

    def set_points(self, x1, y1):
        self.x1, self.y1 = x1, y1
        self._build()

    def set_image_dir(self, image_dir):
        self.image_dir = image_dir
        self._build()

    def set_size(self, size):
        self.size = size
        self._build()

class TC_Sprite(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0,
            sprite: list[int | float, int | float, tuple[int, int, int, int]] = None
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.sprite = sprite
        self._build()

    def _build(self):  
        self.data = []
              
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

        sprite = self.sprite
        if sprite is None: sprite = []

        xCurrent = x1

        for x, y, color in sprite:
            self.add([x + x1, y + y1, color])

    def set_points(self, x1, y1):
        self.x1, self.y1 = x1, y1
        self._build()

    def set_sprite(self, sprite):
        self.sprite = sprite
        self._build()

# ----------
# 3D objects
# ----------

class TC_Point3D(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1, self.z1 = x1, y1, z1
        self.color = color
        self._build()

    def _build(self):
        self.data = []

        x = roundInt(self.x1)
        y = roundInt(self.y1)
        z = float(self.z1)
        color = self.color
        self.add([x, y, color, z])

    def set_points(self, x1, y1, z1):
        self.x1, self.y1 = x1, y1, z1
        self._build()
    

class TC_Line3D(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0,
            x2: int | float = 0, y2: int | float = 0, z2: float = 0,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1, self.z1 = x1, y1, z1
        self.x2, self.y2, self.z2 = x2, y2, z2
        self.color = color
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)
        z1 = float(self.z1)

        x2 = roundInt(self.x2)
        y2 = roundInt(self.y2)
        z2 = float(self.z2)

        color = self.color
     
        dx = abs(x2 - x1)
        sx = 1 if x1 < x2 else -1

        dy = abs(y2 - y1)
        sy = 1 if y1 < y2 else -1

        dz = abs(z2 - z1)
        sz = 1 if z1 < z2 else -1

        dm = max(dx, dy, dz)
        
        ex = ey = ez = dm/2
        for _ in range(dm + 1):
            self.add([x1, y1, color, z1])

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
        self.x1, self.y1, self.z2 = x1, y1, z1
        self.x2, self.y2, self.z2 = x2, y2, z2
        self._build()

class TC_Triangle3D(TC_BaseObject):
    def __init__(
            self,
            x1: int | float = 0, y1: int | float = 0, z1: float = 0, 
            x2: int | float = 0, y2: int | float = 0, z2: float = 0, 
            x3: int | float = 0, y3: int | float = 0, z3: float = 0, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1, self.z1 = x1, y1, z1
        self.x2, self.y2, self.z2 = x2, y2, z2
        self.x3, self.y3, self.z3 = x3, y3, z3
        self.color = color
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)
        z1 = float(self.z1)
        
        x2 = roundInt(self.x2)
        y2 = roundInt(self.y2)
        z2 = float(self.z2)
    
        x3 = roundInt(self.x3)
        y3 = roundInt(self.y3)
        z3 = float(self.z3)

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
                self.add([x, y, color, z])

    def set_points(self, x1, y1, z1, x2, y2, z2, x3, y3, z3):
        self.x1, self.y1, self.z1 = x1, y1, z1
        self.x2, self.y2, self.z2 = x2, y2, z2
        self.x3, self.y3, self.z3 = x3, y3, z3
        self._build()

# ----------
# UI objects
# ----------

class TC_RectangleUI(TC_BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            x2: int | float = 0, y2: int | float = 0, 
            mode: str = "frame",
            char: str = "█",
            color: tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
        self.mode = mode
        self.char = char
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

        x2 = roundInt(self.x2)
        y2 = roundInt(self.y2)

        color = self.color
        mode = self.mode
        char = self.char

        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        
        if mode == "solid":
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self.add([x, y, color, char])

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
                self.add([x, y1, color, top[0] if x==x1 else top[1]])
                self.add([x+1, y2, color, bottom[0] if x+1==x2 else bottom[1]])
            
            for y in range(y1, y2):
                self.add([x1, y+1, color, left[0] if y+1==y2 else left[1]])
                self.add([x2, y, color, right[0] if y==y1 else right[1]])

    def set_points(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self._build()

    def set_mode(self, mode):
        self.mode = mode
        self._build()

    def set_char(self, char):
        self.char = char
        self._build()

class TC_TextUI(TC_BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            message: str = "",
            anchor_x: str = "left",
            max_width: int = None,
            max_height: int = None,
            cutoff: str = "naive",
            color: tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.message = message
        self.anchor_x = anchor_x
        self.color = color
        self.max_width = max_width
        self.max_height = max_height
        self.cutoff = cutoff
        self._build()

    def _build(self):
        self.data = []
        
        x1 = roundInt(self.x1)
        y1 = roundInt(self.y1)

        messages = self.message.split("\n")
        anchor_x = self.anchor_x
        color = self.color
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
                    charIndex = 0
                    message_copy = message
                    while 0 <= charIndex < len(message_copy):
                        charIndex = max_width
                        if charIndex < len(message_copy) and message_copy[charIndex] != " ":
                            while charIndex > 0 and message_copy[charIndex] != " ":
                                charIndex -= 1
                        if charIndex != 0:
                            sepmessages.append(message_copy[:charIndex].lstrip(" "))
                            message_copy = message_copy[charIndex:]
                        else:
                            sepmessages.append(message_copy[:max_width].lstrip(" "))
                            message_copy = message_copy[max_width:]
                    sepmessages.append(message_copy.lstrip(" "))
                            
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
                self.add([x1 + x + xOff, y1 + y, color, char])

            y += 1

    def set_points(self, x1, y1):
        self.x1, self.y1 = x1, y1
        self._build()

    def set_message(self, message):
        self.message = message
        self._build()

    def set_anchor_x(self, anchor_x):
        self.anchor_x = anchor_x
        self._build()

    def set_max_width(self, max_width):
        self.max_width = max_width
        self._build()

    def set_max_height(self, max_height):
        self.max_height = max_height
        self._build()

    def set_cutoff(self, cutoff):
        self.cutoff = cutoff
        self._build()