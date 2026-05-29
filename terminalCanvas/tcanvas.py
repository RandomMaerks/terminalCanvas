import os
import time
import sys
import shutil
import ctypes

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

# ----------------------------
# Predefined display functions
# ----------------------------

def _sanitiseColor(color):
    red = max(min(objects.roundInt(color[0]), 255), 0)
    green = max(min(objects.roundInt(color[1]), 255), 0)
    blue = max(min(objects.roundInt(color[2]), 255), 0)

    return red, green, blue

def _getFGColor(color):
    if color == None: return "\033[38;2;0;0;0m"

    red, green, blue = _sanitiseColor(color)
    return f"\033[38;2;{red};{green};{blue}m"

def _getBGColor(color):
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


    # Display functions
    
    def _plot(self, xIndex, yIndex, color=(0,0,0)):
        x = xIndex + self._xOff
        y = yIndex + self._yOff

        screen = self._screenPixels
        width = self.width
        
        if self._inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = screen[y*width + x]
                alpha = 1/255 * color[3]
                newColor = [
                    (alpha*color[i] + (1-alpha)*colorBelow[i])
                    for i in range(3)
                ]
                color = tuple(newColor)
                
            screen[y*width + x] = (
                objects.roundInt(color[0]),
                objects.roundInt(color[1]),
                objects.roundInt(color[2])
            )

    def draw(self, object):
        plot = self._plot

        for pixel in object.data:
            plot(*pixel)

    def show(self, cursor=False):
        display = [_CURSOR_HOME] if cursor else [_CURSOR_HOME + _CURSOR_HIDE]

        screen = self._screenPixels
        buffer = self._screenBuffer
        width = self.width
        hCenter = self.hCenter
        append = display.append
        sys_write = sys.stdout.write
        sys_flush = sys.stdout.flush

        fg = _getFGColor
        bg = _getBGColor

        last_p1 = screen[0]
        last_p2 = screen[width]

        for y in range(hCenter):
            yIndex = y*2
            row1 = yIndex * width
            row2 = row1 + width

            for x in range(width):
                i1 = row1 + x
                i2 = row2 + x

                p1 = screen[i1]
                p2 = screen[i2]

                b1 = buffer[i1]
                b2 = buffer[i2]

                if not self._buffered:
                    if p1 != last_p1 or p2 != last_p2 or y == 0:
                        append(bg(p2) + fg(p1))
                    append("▀")

                    last_p1 = p1
                    last_p2 = p2
                else:
                    if p1 != b1 or p2 != b2:
                        append(f"\033[{y+1};{x+1}H")
                        append(bg(p2) + fg(p1) + "▀")

            if y < hCenter-1: append("\n")

        append(_COLOR_RESET)

        sys_write(''.join(display))
        sys_flush()

        self._screenBuffer = screen
        self._buffered = True

    def background(self, color: tuple[int, int, int], clear=True):
        self._bgColor = color
        if clear:
            self.clear()

    def clear(self):
        self._screenPixels = [
            self._bgColor for _ in range(self.totalPixels)
            ]

    def end(self):
        print(f"\033[{self.height}H" + _CURSOR_SHOW)


    # Graphical objects

    def point(self, xIndex, yIndex, color=(0,0,0)):
        return objects.TC_Point(xIndex, yIndex, color)

    def line(self, xStart, yStart, xEnd, yEnd, color=(0,0,0)):
        return objects.TC_Line(xStart, yStart, xEnd, yEnd, color)

    def triangle(self, x1, y1, x2, y2, x3, y3, color=(0,0,0)):
        return objects.TC_Triangle(x1, y1, x2, y2, x3, y3, color)

    def rectangle(self, xStart, yStart, xEnd, yEnd, mode="solid", color=(0,0,0)):
        return objects.TC_Rectangle(xStart, yStart, xEnd, yEnd, mode, color)

    def ellipse(self, xStart, yStart, xEnd, yEnd, mode="solid", color=(0,0,0)):
        return objects.TC_Ellipse(xStart, yStart, xEnd, yEnd, mode, color)

    def text(self, xIndex, yIndex, message="", font=None, spacing=0, anchor_x="left", anchor_y="top", color=(0,0,0)):
        return objects.TC_Text(xIndex, yIndex, message, font, spacing, anchor_x, anchor_y, color)

    def image(self, xIndex, yIndex, image_dir, size=None):
        return objects.TC_Image(xIndex, yIndex, image_dir, size)

    def sprite(self, xIndex, yIndex, sprite):
        return objects.TC_Sprite(xIndex, yIndex, sprite)
        
            
    # Canvas transformation
    
    def flip(self, direction: str = None):
        width = self.width
        height = self.height
        screen = self._screenPixels

        if direction in ["h", "horizontal", "y"]:
            screen = [
                [
                    screen[y*width + width-x-1] 
                    for x in range(width)
                ]
                for y in range(height)
                ]
        elif direction in ["v", "vertical", "x"]:
            screen = [
                [
                    screen[(height-y-1)*width + x]
                    for x in range(width)
                ]
                for y in range(height)
                ]
        else:
            screen = [
                [
                    screen[(height-y-1)*width + width-x-1]
                    for x in range(width)
                ]
                for y in range(height)
                ]

    def translate(self, xIndex, yIndex):
        self._xOff = int(xIndex)
        self._yOff = int(yIndex)


    # Save image

    def save(self, name=None, ext=".png", dir=""):
        if name is None:
            name = time.strftime("%Y_%m_%d %H_%M_%S", time.localtime())
            
        toNPArray = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        width = self.width
        height = self.height
        for y in range(height):
            for x in range(width):
                red, green, blue = self._screenPixels[y*width + x]
                alpha = 255
                toNPArray[y, x] = np.array([red, green, blue, alpha])

        newImage = Image.fromarray(toNPArray)
        newImage.save(dir + name + ext)

    
    # Input

    def keyPressed(self, key, map=VK):
        try:
            return ctypes.windll.user32.GetAsyncKeyState(map[key]) & 0x8000
        except KeyError as e:
            raise KeyError(f"Key {key} has not been configured. ({repr(e)})")
        

    # Other functions
        
    def _inRange(self, xIndex, yIndex, xRStart=None, xREnd=None, yRStart=None, yREnd=None):
        if not xRStart: xRStart = 0
        if not xREnd: xREnd = self.width
        if not yRStart: yRStart = 0
        if not yREnd: yREnd = self.height
        return xIndex in range(xRStart, xREnd) and yIndex in range(yRStart, yREnd)

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
    
    def _plot(self, xIndex, yIndex, color=(0,0,0), zIndex=None):
        x = xIndex + self._xOff
        y = yIndex + self._yOff

        if len(color) < 3:
            raise Exception("Missing color arguments. Must be an iterable with RGB values.")
        
        if self._inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = self._screenPixels[y*self.width + x]
                alpha = 1/255 * color[3]
                newColor = [
                    alpha*color[i] + (1-alpha)*colorBelow[i]
                    for i in range(3)
                ]
                color = tuple(newColor)
                
            if zIndex is not None:
                if zIndex < self.depthBuffer[y, x]:
                    self.depthBuffer[y, x] = zIndex
                    self._screenPixels[y*self.width + x] = (
                        objects.roundInt(color[0] * (1 - self.depthIntensity * zIndex)),
                        objects.roundInt(color[1] * (1 - self.depthIntensity * zIndex)),
                        objects.roundInt(color[2] * (1 - self.depthIntensity * zIndex))
                    )
            else:
                self._screenPixels[y*self.width + x] = (
                    objects.roundInt(color[0]),
                    objects.roundInt(color[1]),
                    objects.roundInt(color[2])
                )
                
    def resetDepthBuffer(self):
        self.depthBuffer = np.full((self.height, self.width), np.inf)

    # Graphical objects

    def triangle3D(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, color=(0,0,0)):
        return objects.TC_Triangle3D(x1, y1, z1, x2, y2, z2, x3, y3, z3, color)