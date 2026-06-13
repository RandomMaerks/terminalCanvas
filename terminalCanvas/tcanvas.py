import os
import time
import sys
import shutil
import ctypes
from ctypes import wintypes

from PIL import Image
import numpy as np

from . import objects
from .vk import VK

os.system("")

# ---------------------
# ANSI escape sequences
# ---------------------

_COLOR_RESET = "\033[38;2;255;255;255m\033[48;2;0;0;0m"
_CURSOR_HOME = "\033[H"
_CURSOR_SHOW = "\033[?25h"
_CURSOR_HIDE = "\033[?25l"
_SCREEN_CLEAR = "\033[2J"

# --------------
# Caching ctypes
# --------------

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

# ----------------------------
# Predefined display functions
# ----------------------------

def _sanitiseColor(color: tuple[int, int, int]) -> tuple[int, int, int]:
    red = max(min(objects.roundInt(color[0]), 255), 0)
    green = max(min(objects.roundInt(color[1]), 255), 0)
    blue = max(min(objects.roundInt(color[2]), 255), 0)

    return red, green, blue

def _getFGColor(color: tuple[int, int, int]) -> str:
    if color == None: return "\033[38;2;0;0;0m"

    red, green, blue = _sanitiseColor(color)
    return f"\033[38;2;{red};{green};{blue}m"

def _getBGColor(color: tuple[int, int, int]) -> str:
    if color == None: return "\033[48;2;0;0;0m"

    red, green, blue = _sanitiseColor(color)
    return f"\033[48;2;{red};{green};{blue}m"

# ---------------
# Terminal canvas
# ---------------

class TCanvas:
    def __init__(
            self,
            width: int = None, 
            height: int = None
    ) -> None:

        if width == None:
            self.width, _ = shutil.get_terminal_size()
        else:
            self.width = width

        if height == None:
            _, self.height = shutil.get_terminal_size()
            self.height *= 2
        else:
            self.height = height

        self.totalPixels = self.width * self.height

        self.wCenter = self.width//2
        self.hCenter = self.height//2

        self._screenPixels = []
        self._screenBuffer = []

        self._xOff = 0
        self._yOff = 0

        self._bgColor = (255, 255, 255)

        #print(_SCREEN_CLEAR)
        self.clear()
        self._screenBuffer = self._screenPixels
        self._buffered = False

        self._lastKeyPressed = {}


    # Display functions
    
    def _plot(
            self,
            xIndex: int, yIndex: int, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255)
    ) -> None:
        x = xIndex + self._xOff
        y = yIndex + self._yOff

        width = self.width
        
        if self._inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = self._screenPixels[y*width + x]
                alpha = 1/255 * color[3]
                newColor = [
                    (alpha*color[i] + (1-alpha)*colorBelow[i])
                    for i in range(3)
                ]
                color = tuple(newColor)
                
            self._screenPixels[y*width + x] = (
                objects.roundInt(color[0]),
                objects.roundInt(color[1]),
                objects.roundInt(color[2])
            )

    def draw(self, object) -> None:
        plot = self._plot

        for pixel in object.data:
            plot(*pixel)

    def show(self, cursor=False) -> None:
        display = [_CURSOR_HOME] if cursor else [_CURSOR_HOME + _CURSOR_HIDE]

        width = self.width
        hCenter = self.hCenter
        append = display.append
        sys_write = sys.stdout.write
        sys_flush = sys.stdout.flush

        fg = _getFGColor
        bg = _getBGColor

        last_p1 = None
        last_p2 = None

        for y in range(hCenter):
            yIndex = y*2
            row1 = yIndex * width
            row2 = row1 + width

            for x in range(width):
                i1 = row1 + x
                i2 = row2 + x

                p1 = self._screenPixels[i1]
                p2 = self._screenPixels[i2]

                b1 = self._screenBuffer[i1]
                b2 = self._screenBuffer[i2]

                if not self._buffered:
                    if p1 != last_p1 or p2 != last_p2 or y == 0:
                        append(bg(p2) + fg(p1))
                    append("▀")

                    last_p1 = p1
                    last_p2 = p2
                else:
                    if p1 != b1 or p2 != b2:
                        append(f"\033[{y+1};{x+1}H")
                        append(fg(p1))
                        append(bg(p2))
                        append("▀")

            if y < hCenter-1: append("\n")

        append(_COLOR_RESET)

        sys_write(''.join(display))
        sys_flush()

        self._screenBuffer = list(self._screenPixels)
        self._buffered = True

    def background(self, color: tuple[int, int, int], clear=True) -> None:
        self._bgColor = color
        if clear:
            self.clear()

    def clear(self) -> None:
        self._screenPixels = [
            self._bgColor for _ in range(self.totalPixels)
            ]

    def end(self) -> None:
        print(f"\033[{self.height}H" + _CURSOR_SHOW)

    def space(self) -> tuple[int, int]:
        xMin, xMax = 0 - self._xOff, self.width - self._xOff
        yMin, yMax = 0 - self._yOff, self.height - self._yOff
        for y in range(yMin, yMax):
            for x in range(xMin, xMax):
                yield (x, y)


    # Graphical objects

    def point(
            self,
            x1: int | float, y1: int | float,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> objects.TC_Point:
        return objects.TC_Point(x1, y1, color)

    def line(
            self,
            x1: int | float, y1: int | float,
            x2: int | float, y2: int | float,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> objects.TC_Line:
        return objects.TC_Line(x1, y1, x2, y2, color)

    def triangle(
            self,
            x1: int | float, y1: int | float,
            x2: int | float, y2: int | float,
            x3: int | float, y3: int | float,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> objects.TC_Triangle:
        return objects.TC_Triangle(x1, y1, x2, y2, x3, y3, color)

    def rectangle(
            self, 
            x1: int | float, y1: int | float, 
            x2: int | float, y2: int | float, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> objects.TC_Rectangle:
        return objects.TC_Rectangle(x1, y1, x2, y2, mode, color)

    def ellipse(
            self,
            x1: int | float, y1: int | float, 
            x2: int | float, y2: int | float, 
            mode: str = "solid", 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> objects.TC_Ellipse:
        return objects.TC_Ellipse(x1, y1, x2, y1, mode, color)

    def text(
            self, 
            x1: int | float, y1: int | float, 
            message: str = "",
            font: dict = None, 
            spacing: int = 0,
            anchor_x: str = "left",
            anchor_y: str = "top",
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> objects.TC_Text:
        return objects.TC_Text(x1, y1, message, font, spacing, anchor_x, anchor_y, color)

    def image(
            self,
            x1: int | float, y1: int | float,
            image_dir: str,
            size: tuple[int, int] | None = None
    ) -> objects.TC_Image:
        return objects.TC_Image(x1, y1, image_dir, size)

    def sprite(
            self,
            x1: int | float, y1: int | float,
            sprite: list[int | float, int | float, tuple[int, int, int, int]]
    ) -> objects.TC_Sprite:
        return objects.TC_Sprite(x1, y1, sprite)
        
            
    # Canvas transformation
    
    def flip(self, direction: str = None) -> None:
        width = self.width
        height = self.height

        if direction in ["h"]:
            self._screenPixels = [
                self._screenPixels[y*width + x] 
                for y in range(height)                
                for x in reversed(range(width))
                ]
        elif direction in ["v"]:
            self._screenPixels = [
                self._screenPixels[y*width + x]
                for y in reversed(range(height))
                for x in range(width)
                ]
        else:
            self._screenPixels = [
                self._screenPixels[y*width + x]
                for y in reversed(range(height))
                for x in reversed(range(width))
                ]

    def translate(self, xIndex: int | float, yIndex: int | float) -> None:
        self._xOff = int(xIndex)
        self._yOff = int(yIndex)


    # Save image

    def save(self, name: str, size: int = None) -> None:
        toNPArray = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        width = self.width
        height = self.height
        for y in range(height):
            for x in range(width):
                red, green, blue = self._screenPixels[y*width + x]
                alpha = 255
                toNPArray[y, x] = np.array([red, green, blue, alpha])

        newImage = Image.fromarray(toNPArray)
        if size is not None:
            newImage = newImage.resize(
                (newImage.width * size, newImage.height * size),
                Image.Resampling.NEAREST
                )
        newImage.save(name)

    
    # Keyboard & mouse input

    def keyPressed(self, key: str, map: dict = VK, hold: bool = True) -> bool:
        vk = map.get(key)
        if vk is None:
            raise KeyError(f"Key {key} has not been defined in selected map.")

        current = bool(_user32.GetAsyncKeyState(vk) & 0x8000)
        previous = self._lastKeyPressed.get(vk, False)

        self._lastKeyPressed[vk] = current

        if hold is True:
            return current
        else:
            return current and not previous

    class _point_t(ctypes.Structure):
        _fields_ = [
            ('x', ctypes.c_long),
            ('y', ctypes.c_long)
        ]

    def getMousePos(self) -> tuple[int, int] | None:
        point = self._point_t()
        if not _user32.GetCursorPos(ctypes.pointer(point)):
            return None

        hwnd = _kernel32.GetConsoleWindow()
        if not hwnd:
            return None

        # Get literal coordinates (device resolution)
        origin = wintypes.POINT(0, 0)
        if not _user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            return None

        client = wintypes.RECT()
        if not _user32.GetClientRect(hwnd, ctypes.byref(client)):
            return None

        if client.right == 0 or client.bottom == 0:
            return None

        # Map to canvas coordinates (canvas resolution)
        wx = client.right // self.width * self.width
        wy = client.bottom // self.height * self.height

        mx = (point.x - origin.x) / wx * self.width
        my = (point.y - origin.y) / wy * self.height

        return int(mx), int(my)

    # Other functions
        
    def _inRange(
            self,
            xIndex: int, yIndex: int, 
            xStart: int = 0, xEnd: int = None,
            yStart: int = 0, yEnd: int = None
    ) -> True | False:
        if xEnd is None: xEnd = self.width
        if yEnd is None: yEnd = self.height
        return xStart <= xIndex < xEnd and yStart <= yIndex < yEnd

# ----------------------------
# Terminal canvas, 3D pipeline
# ----------------------------

class TCanvas3D(TCanvas):
    def __init__(
            self,
            width: int = None, 
            height: int = None
    ) -> None:

        super().__init__(width, height)

        self.depthIntensity = 0
        self.resetDepthBuffer()
        
        
    # Display functions
    
    def _plot(
            self,
            xIndex: int, yIndex: int, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255), 
            zIndex: float = None
    ) -> None:
        x = xIndex + self._xOff
        y = yIndex + self._yOff

        width = self.width
        depthIntensity = self.depthIntensity

        if len(color) < 3:
            raise Exception("Missing color arguments. Must be an iterable with RGB values.")
        
        if self._inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = self._screenPixels[y*width + x]
                alpha = 1/255 * color[3]
                newColor = [
                    alpha*color[i] + (1-alpha)*colorBelow[i]
                    for i in range(3)
                ]
                color = tuple(newColor)
                
            if zIndex is not None:
                if zIndex < self.depthBuffer[y, x]:
                    self.depthBuffer[y, x] = zIndex
                    self._screenPixels[y*width + x] = (
                        objects.roundInt(color[0] * (1 - depthIntensity * zIndex)),
                        objects.roundInt(color[1] * (1 - depthIntensity * zIndex)),
                        objects.roundInt(color[2] * (1 - depthIntensity * zIndex))
                    )
            else:
                self._screenPixels[y*width + x] = (
                    objects.roundInt(color[0]),
                    objects.roundInt(color[1]),
                    objects.roundInt(color[2])
                )
                
    def resetDepthBuffer(self) -> None:
        self.depthBuffer = np.full((self.height, self.width), np.inf)

    # Graphical objects

    def triangle3D(
            self,
            x1: int | float, y1: int | float, z1: float, 
            x2: int | float, y2: int | float, z2: float, 
            x3: int | float, y3: int | float, z3: float, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> objects.TC_Triangle3D:
        return objects.TC_Triangle3D(x1, y1, z1, x2, y2, z2, x3, y3, z3, color)