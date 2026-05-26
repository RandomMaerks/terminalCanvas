from PIL import Image

# -----------------
# Base object class
# -----------------

class BaseObject():
    def __init__(self) -> None:
        self.data = []

    # Pixel insertion, early removal

    def add(self, pixel: list) -> None:
        self.data.append(pixel)

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

# ------------------
# Predefined objects
# ------------------
    
class TC_Point(BaseObject):
    def __init__(
            self,
            xIndex: int | float,
            yIndex: int | float,
            color: tuple(int, int, int, int) = (0, 0, 0, 255),
    ) -> None:

        super().__init__()
        
        x = roundInt(xIndex)
        y = roundInt(yIndex)
        self.add([x, y, color])

class TC_Line(BaseObject):
    def __init__(
            self,
            xStart: int | float,
            yStart: int | float,
            xEnd: int | float, 
            yEnd: int | float,
            color: tuple(int, int, int, int) = (0, 0, 0, 255),
    ) -> None:

        super().__init__()
        
        xStart = roundInt(xStart)
        yStart = roundInt(yStart)

        xEnd = roundInt(xEnd)
        yEnd = roundInt(yEnd)
        
        if abs(xEnd - xStart) > abs(yEnd - yStart):
            if xEnd < xStart:
                xStart, xEnd = xEnd, xStart
                yStart, yEnd = yEnd, yStart
            dx = xEnd - xStart
            dy = yEnd - yStart
            yi = 1
            if dy < 0:
                yi = -1
                dy = -dy
            D = (2 * dy) - dx
            y = yStart

            for x in range(xStart, xEnd + 1):
                self.add([x, y, color])
                if D > 0:
                    y += yi
                    D += 2*(dy - dx)
                else:
                    D += 2*dy
        else:
            if yEnd < yStart:
                xStart, xEnd = xEnd, xStart
                yStart, yEnd = yEnd, yStart
            dx = xEnd - xStart
            dy = yEnd - yStart
            xi = 1
            if dx < 0:
                xi = -1
                dx = -dx
            D = (2 * dx) - dy
            x = xStart

            for y in range(yStart, yEnd + 1):
                self.add([x, y, color])
                if D > 0:
                    x += xi
                    D += 2*(dx - dy)
                else:
                    D += 2*dx

class TC_Triangle(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float,
            x2: int | float, y2: int | float,
            x3: int | float, y3: int | float,
            color: tuple(int, int, int, int) = (0, 0, 0, 255),
    ) -> None:

        super().__init__()
        
        x1 = roundInt(x1)
        y1 = roundInt(y1)
        
        x2 = roundInt(x2)
        y2 = roundInt(y2)
    
        x3 = roundInt(x3)
        y3 = roundInt(y3)

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
        if x13[m] < x123[m]:
            xLeft, xRight = x13, x123
        else:
            xLeft, xRight = x123, x13

        for y in range(y1, y3 + 1):
            i = y - y1
            left = xLeft[i]
            right = xRight[i]
            for x in range(left, right + 1):
                self.add([x, y, color])


class TC_Triangle3D(BaseObject):
    def __init__(
            self,
            x1: int | float, y1: int | float, z1: int | float, 
            x2: int | float, y2: int | float, z2: int | float, 
            x3: int | float, y3: int | float, z3: int | float, 
            color: tuple(int, int, int, int) = (0, 0, 0, 255),
    ) -> None:

        super().__init__()
        
        x1 = roundInt(x1)
        y1 = roundInt(y1)
        z1 = float(z1)
        
        x2 = roundInt(x2)
        y2 = roundInt(y2)
        z2 = float(z2)
    
        x3 = roundInt(x3)
        y3 = roundInt(y3)
        z3 = float(z3)

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

class TC_Rectangle(BaseObject):
    def __init__(
            self, 
            xStart: int | float, yStart: int | float, 
            xEnd: int | float, yEnd: int | float, 
            mode: str = "solid", 
            color: tuple(int, int, int, int) = (0, 0, 0, 255),
    ) -> None:

        super().__init__()
        
        xStart = roundInt(xStart)
        yStart = roundInt(yStart)

        xEnd = roundInt(xEnd)
        yEnd = roundInt(yEnd)

        if xStart > xEnd:
            xStart, xEnd = xEnd, xStart
        if yStart > yEnd:
            yStart, yEnd = yEnd, yStart
        
        if mode == "solid":
            for y in range(yStart, yEnd + 1):
                for x in range(xStart, xEnd + 1):
                    self.add([x, y, color])

        elif mode == "outline":
            for x in range(xStart, xEnd + 1):
                self.add([x, yStart, color])
                self.add([x, yEnd, color])

            for y in range(yStart + 1, yEnd):
                self.add([xStart, y, color])
                self.add([xEnd, y, color])

class TC_Ellipse(BaseObject):
    def __init__(
            self,
            xStart: int | float, yStart: int | float, 
            xEnd: int | float, yEnd: int | float, 
            mode: str = "solid", 
            color: tuple(int, int, int, int) = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        xStart = roundInt(xStart)
        yStart = roundInt(yStart)

        xEnd = roundInt(xEnd)
        yEnd = roundInt(yEnd)

        if xStart > xEnd: xStart, xEnd = xEnd, xStart
        if yStart > yEnd: yStart, yEnd = yEnd, yStart

        xRange = xEnd - xStart
        yRange = yEnd - yStart

        if xRange == 0 or yRange == 0: return

        rx = xRange // 2
        ry = yRange // 2

        if mode == "solid":
            for y in range(0, ry+1):
                xPos = roundInt(xRange/2 * (1 - (2*y/yRange)*(2*y/yRange))**0.5)
                xNeg = -xPos
                for x in range(xNeg, xPos+1):
                    self.add([x + xStart + rx, y + yStart + ry, color])
                    if y != 0:
                        self.add([x + xStart + rx, -y + yStart + ry, color])

        elif mode == "outline":
            for y in range(0, ry+1):
                x = roundInt(xRange/2 * (1 - (2*y/yRange)*(2*y/yRange))**0.5)
                self.add([x + xStart + rx, y + yStart + ry, color])
                self.add([-x + xStart + rx, y + yStart + ry, color])
                self.add([x + xStart + rx, -y + yStart + ry, color])
                self.add([-x + xStart + rx, -y + yStart + ry, color])

            for x in range(0, rx+1):
                y = roundInt(yRange/2 * (1 - (2*x/xRange)*(2*x/xRange))**0.5)
                self.add([x + xStart + rx, y + yStart + ry, color])
                self.add([-x + xStart + rx, y + yStart + ry, color])
                self.add([x + xStart + rx, -y + yStart + ry, color])
                self.add([-x + xStart + rx, -y + yStart + ry, color])

class TC_Text(BaseObject):
    def __init__(
            self, 
            xIndex: int | float, yIndex: int | float, 
            message: str = "",
            font = None, 
            spacing: int = 0,
            anchor_x: str = "left",
            anchor_y: str = "top",
            color: tuple(int, int, int, int) = (0, 0, 0, 255),
    ) -> None:

        super().__init__()
        
        if font is None: return

        xIndex = roundInt(xIndex)
        yIndex = roundInt(yIndex)

        xCurrent = xIndex

        textLines = []
        totalWidth = 0

        kerningInfo = font.get("kerning")

        for index, char in enumerate(message):
            if char not in font:
                xCurrent += 4 + spacing
                totalWidth += 4 + spacing
                continue

            glyph = font.get(char)
            charWidth = len(glyph[0])

            if index > 0 and kerningInfo is not None:
                kern = kerningInfo.get(f"{message[index-1]}{char}", 0)
            else:
                kern = 0

            for y, row in enumerate(glyph):
                line = []
                for x, data in enumerate(row):
                    line.append([data, xCurrent + x + kern, yIndex + y, color])
                textLines.append(line)

            xCurrent += charWidth + spacing + kern
            totalWidth += charWidth + spacing + kern

        if anchor_x == "left": xOff = 0
        elif anchor_x == "center": xOff = -(totalWidth)//2
        elif anchor_x == "right": xOff = -(totalWidth)

        if anchor_y == "top": yOff = 0
        elif anchor_y == "center": yOff = -len(textLines[0])//2
        elif anchor_y == "bottom": yOff = -len(textLines[0])

        for line in textLines:
            for data, x, y, color in line:
                if data == "1": self.add([x + xOff, y + yOff, color])

class TC_Image(BaseObject):
    def __init__(
            self,
            xIndex: int | float, yIndex: int | float,
            image_dir: str,
            size: float | None = None
    ) -> None:

        super().__init__()
        
        xIndex = roundInt(xIndex)
        yIndex = roundInt(yIndex)

        img = Image.open(image_dir)
        if size is not None:
            img = img.resize(tuple(size))
        res = np.asarray(img)

        for y in range(len(res)):
            for x, color in enumerate(res[y]):
                self.add([x + xIndex, y + yIndex, tuple(color)])

class TC_Sprite(BaseObject):
    def __init__(
            self,
            xIndex: int | float, yIndex: int | float,
            sprite: list[int | float, int | float, tuple(int, int, int, int)]
    ) -> None:

        super().__init__()
        
        xIndex = roundInt(xIndex)
        yIndex = roundInt(yIndex)

        xCurrent = xIndex

        for x, y, color in sprite:
            self.add([x + xIndex, y + yIndex, color])