from PIL import Image
import numpy as np

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

class BaseObject:
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
        for x, y, _ in self.data:
            x += xShift
            y += yShift

    def scale(self, amount: int) -> None:
        xTop, yTop, _ = min(self.data)
        scaled = []
        for x, y, color in self.data:
            for i in range(amount):
                for j in range(amount):
                    xShift = (x-xTop) * (amount-1)
                    yShift = (y-yTop) * (amount-1)
                    scaled.append([x + i + xShift, y + j + yShift, color])
        self.data = scaled

    def set_color(self, color: tuple[int, int, int, int]) -> None:
        self.color = color
        self._build()

# ----------
# 2D objects
# ----------
    
class TC_Point(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float,
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
    

class TC_Line(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float,
            x2: int | float, y2: int | float,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
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

    def set_points(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self._build()

class TC_Triangle(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float,
            x2: int | float, y2: int | float,
            x3: int | float, y3: int | float,
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

class TC_Rectangle(BaseObject):
    def __init__(
            self, 
            x1: int | float, y1: int | float, 
            x2: int | float, y2: int | float, 
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

class TC_Ellipse(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float, 
            x2: int | float, y2: int | float, 
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

        if mode == "outline":
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

        elif mode == "solid":
            if rx2 == 0 or ry2 == 0: return

            for y in range(-ry, ry + 1):
                xMax = roundInt(rx * (1 - (y*y)/(ry2))**0.5)

                for x in range(-xMax, xMax+1):
                    self.add([cx + x, cy + y, color])

    def set_points(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self._build()

class TC_Text(BaseObject):
    def __init__(
            self, 
            x1: int | float, y1: int | float, 
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

        if font is None: return  

        kerningInfo = font.get("kerning")
        next_xInfo = font.get("next_x", dict())
        
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

                if index > 0 and kerningInfo is not None:
                    kern = kerningInfo.get(f"{message[index-1]}{char}", 0)
                else:
                    kern = 0

                for y, row in enumerate(glyph):
                    line = []
                    for x, data in enumerate(row):
                        line.append([data, xCurrent + x + kern, yCurrent + y, color])
                    textLines.append(line)

                xCurrent += charWidth + spacing + kern + next_x
                totalWidth += charWidth + spacing + kern + next_x
            
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


class TC_Image(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float,
            image_dir: str,
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

class TC_Sprite(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float,
            sprite: list[int | float, int | float, tuple[int, int, int, int]]
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

class TC_Triangle3D(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float, z1: float, 
            x2: int | float, y2: int | float, z2: float, 
            x3: int | float, y3: int | float, z3: float, 
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