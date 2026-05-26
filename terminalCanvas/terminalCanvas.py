import os
import random
import time
import sys
import shutil
from PIL import Image
import numpy as np
import ctypes

os.system("")


"""
--- terminalCanvas Python Module ---

Author: RandomMaerks
Description: A module for creating a canvas and displaying text-based graphics in the terminal
License: MIT License

Credits:   1. Gabriel Gambetta's book "Computer Graphics from Scratch"
           (https://www.gabrielgambetta.com/computer-graphics-from-scratch)
"""



# ---------------------
# ANSI escape sequences
# ---------------------

COLOR_RESET = "\033[38;2;255;255;255m\033[48;2;0;0;0m"
CURSOR_HOME = "\033[H"
CURSOR_SHOW = "\033[?25h"
CURSOR_HIDE = "\033[?25l"
SCREEN_CLEAR = "\033[2J"

# ----------------------------
# Predefined display functions
# ----------------------------

def getFGColor(color):
    if color == None: return "\033[38;2;0;0;0m"

    red = roundInt(color[0])
    green = roundInt(color[1])
    blue = roundInt(color[2])
    return f"\033[38;2;{red};{green};{blue}m"

def getBGColor(color):
    if color == None: return "\033[48;2;0;0;0m"

    red = roundInt(color[0])
    green = roundInt(color[1])
    blue = roundInt(color[2])
    return f"\033[48;2;{red};{green};{blue}m"

# --------------
# Alias for keys
# --------------

VK = {
    "LMOUSE": 0x01,    "RMOUSE": 0x02,    "MMOUSE": 0x04,
    "BACK": 0x08,    "TAB": 0x09,    "SHIFT": 0x10,    "CTRL": 0x11,    "ALT": 0x12,
    "CAPS": 0x14,    "ESC": 0x1B,    "SPACE": 0x20,    "PGUP": 0x21,    "PGDN": 0x22,
    "END": 0x23,    "HOME": 0x24,
    "LEFT": 0x25,    "UP": 0x26,    "RIGHT": 0x27,    "DOWN": 0x28,
    "PRTSC": 0x2C,    "INSERT": 0x2D,    "DELETE": 0x2E,
    
    "0": 0x30,    "1": 0x31,    "2": 0x32,    "3": 0x33,    "4": 0x34,
    "5": 0x35,    "6": 0x36,    "7": 0x37,    "8": 0x38,    "9": 0x39,
    
    "A": 0x41,    "B": 0x42,    "C": 0x43,    "D": 0x44,    "E": 0x45,    "F": 0x46,    "G": 0x47,
    "H": 0x48,    "I": 0x49,    "J": 0x4A,    "K": 0x4B,    "L": 0x4C,    "M": 0x4D,    "N": 0x4E,
    "O": 0x4F,    "P": 0x50,    "Q": 0x51,    "R": 0x52,    "S": 0x53,    "T": 0x54,    "U": 0x55,
    "V": 0x56,    "W": 0x57,    "X": 0x58,    "Y": 0x59,    "Z": 0x5A,
    
    "LWIN": 0x5B,    "RWIN": 0x5C,    "SLEEP": 0x5F,
    "NUMPAD0": 0x60,    "NUMPAD1": 0x61,    "NUMPAD2": 0x62,    "NUMPAD3": 0x63,    "NUMPAD4": 0x64,
    "NUMPAD5": 0x65,    "NUMPAD6": 0x66,    "NUMPAD7": 0x67,    "NUMPAD8": 0x68,    "NUMPAD9": 0x69,
    "MULTIPLY": 0x6A,    "ADD": 0x6B,    "SEPARATOR": 0x6C,    "SUBTRACT": 0x6D,    "DECIMAL": 0x6E,    "DIVIDE": 0x6F,
    
    "F1": 0x70,    "F2": 0x71,    "F3": 0x72,    "F4": 0x73,    "F5": 0x74,
    "F6": 0x75,    "F7": 0x76,    "F8": 0x77,    "F9": 0x78,    "F10": 0x79,
    "F11": 0x7A,    "F12": 0x7B,    "F13": 0x7C,    "F14": 0x7D,    "F15": 0x7E,
    "F16": 0x7F,    "F17": 0x80,    "F18": 0x81,    "F19": 0x82,    "F20": 0x83,
    "F21": 0x84,    "F22": 0x85,    "F23": 0x86,    "F24": 0x87,
    
    "NUMLOCK": 0x90,    "SCROLL": 0x91,    "LSHIFT": 0xA0,    "RSHIFT": 0xA1,
    "LCONTROL": 0xA2,    "RCONTROL": 0xA3,    "LMENU": 0xA4,    "RMENU": 0xA5,
}

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

def roundInt(number):
    try:
        return int(round(number, 0))
    except TypeError as e:
        raise TypeError(repr(e) + f" (offender: {number})")

# -----------------
# Base object class
# -----------------

class BaseObject():
    def __init__(self):
        self.data = []
        self.reset = True

    # Pixel insertion, early removal

    def add(self, pixel: list):
        self.data.append(pixel)

    # Object transformation

    def move(self, xShift: int, yShift: int):
        for x, y, _ in self.data:
            x += xShift
            y += yShift

    def scale(self, amount: int):
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
    def __init__(self, xIndex, yIndex, color):
        super().__init__()
        self.new(xIndex, yIndex, color)

    def new(self, xIndex, yIndex, color=(0,0,0)):
        if self.reset == True: self.data = []
        
        x = roundInt(xIndex)
        y = roundInt(yIndex)
        self.add([x, y, color])

class TC_Line(BaseObject):
    def __init__(self, xStart, yStart, xEnd, yEnd, color):
        super().__init__()
        self.new(xStart, yStart, xEnd, yEnd, color)

    def new(self, xStart, yStart, xEnd, yEnd, color=(0,0,0)):
        if self.reset == True: self.data = []
        
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
    def __init__(self, x1, y1, x2, y2, x3, y3, color):
        super().__init__()
        self.new(x1, y1, x2, y2, x3, y3, color)

    def new(self, x1, y1, x2, y2, x3, y3, color=(0,0,0)):
        if self.reset == True: self.data = []
        
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

        # Compute the x-coords
        x12 = interpolate(y1, x1, y2, x2)
        x23 = interpolate(y2, x2, y3, x3)
        x13 = interpolate(y1, x1, y3, x3)

        # Concatenate the short sides
        x12.pop(-1)
        x123 = x12 + x23

        # Determine which is left and which is right
        m = len(x123) // 2
        if x13[m] < x123[m]: xLeft, xRight = x13, x123
        else: xLeft, xRight = x123, x13

        # Draw the horizontal segments
        for y in range(y1, y3 + 1):
            i = y - y1
            left = xLeft[i]
            right = xRight[i]
            for x in range(left, right + 1):
                self.add([x, y, color])
        

    def fillBottom(self, x1, y1, x2, y2, x3, y3, color):
        invslope1 = (x2 - x1) / (y2 - y1)
        invslope2 = (x3 - x1) / (y3 - y1)

        curx1, curx2 = x1, x1

        for y in range(y1, y2+1):
            left = int(curx1)
            right = int(curx2)
            if left > right: left, right = right, left
            for x in range(left, right+1):
                self.add([x, y, color])
            curx1 += invslope1
            curx2 += invslope2

    def fillTop(self, x1, y1, x2, y2, x3, y3, color):
        invslope1 = (x3 - x1) / (y3 - y1)
        invslope2 = (x3 - x2) / (y3 - y2)

        curx1, curx2 = x3, x3

        for y in range(y3, y1-1, -1):
            left = int(curx1)
            right = int(curx2)
            if left > right: left, right = right, left
            for x in range(left, right+1):
                self.add([x, y, color])
            curx1 -= invslope1
            curx2 -= invslope2


class TC_Triangle3D(BaseObject):
    def __init__(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, color):
        super().__init__()
        self.new(x1, y1, z1, x2, y2, z2, x3, y3, z3, color)

    def new(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, color=(0,0,0)):
        if self.reset == True: self.data = []
        
        x1 = roundInt(x1)
        y1 = roundInt(y1)
        z1 = float(z1)
        
        x2 = roundInt(x2)
        y2 = roundInt(y2)
        z2 = float(z2)
    
        x3 = roundInt(x3)
        y3 = roundInt(y3)
        z3 = float(z3)

        # Sort the points
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

        # Compute the x-coords and z-coords
        x12 = interpolate(y1, x1, y2, x2)
        x23 = interpolate(y2, x2, y3, x3)
        x13 = interpolate(y1, x1, y3, x3)

        z12 = interpolate(y1, z1, y2, z2, round=False)
        z23 = interpolate(y2, z2, y3, z3, round=False)
        z13 = interpolate(y1, z1, y3, z3, round=False)

        # Concatenate the short sides
        x12.pop(-1)
        x123 = x12 + x23

        z12.pop(-1)
        z123 = z12 + z23

        # Determine which is left and which is right
        m = len(x123) // 2
        if x13[m] < x123[m]:
            xLeft, xRight = x13, x123
            zLeft, zRight = z13, z123
        else:
            xLeft, xRight = x123, x13
            zLeft, zRight = z123, z13

        # Draw the horizontal segments
        for y in range(y1, y3 + 1):
            i = y - y1
            left = xLeft[i]
            right = xRight[i]
            zSegment = interpolate(left, zLeft[i], right, zRight[i], round=False)
            for x in range(left, right + 1):
                z = zSegment[x-left]
                self.add([x, y, color, z])

class TC_Rectangle(BaseObject):
    def __init__(self, xStart, yStart, xEnd, yEnd, mode, color):
        super().__init__()
        self.new(xStart, yStart, xEnd, yEnd, mode, color)

    def new(self, xStart, yStart, xEnd, yEnd, mode="solid", color=(0,0,0)):
        if self.reset == True: self.data = []
        
        xStart = roundInt(xStart)
        yStart = roundInt(yStart)

        xEnd = roundInt(xEnd)
        yEnd = roundInt(yEnd)

        if xStart > xEnd: xStart, xEnd = xEnd, xStart
        if yStart > yEnd: yStart, yEnd = yEnd, yStart
        
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
    def __init__(self, xStart, yStart, xEnd, yEnd, mode, color):
        super().__init__()
        self.new(xStart, yStart, xEnd, yEnd, mode, color)

    def new(self, xStart, yStart, xEnd, yEnd, mode="solid", color=(0,0,0)):
        if self.reset == True: self.data = []

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
                    if y != 0: self.add([x + xStart + rx, -y + yStart + ry, color])
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
    def __init__(self, xIndex, yIndex, message, font, spacing, anchor_x, anchor_y, color):
        super().__init__()
        self.new(xIndex, yIndex, message, font, spacing, anchor_x, anchor_y, color)

    def new(self, xIndex, yIndex, message, font=None, spacing=0, anchor_x="left", anchor_y="top", color=(0,0,0)):
        if self.reset == True: self.data = []
        
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
    def __init__(self, xIndex, yIndex, image_dir, size):
        super().__init__()
        self.new(xIndex, yIndex, image_dir, size)

    def new(self, xIndex, yIndex, image_dir, size=None):
        if self.reset == True: self.data = []
        
        xIndex = roundInt(xIndex)
        yIndex = roundInt(yIndex)

        img = Image.open(image_dir)
        if size is not None: img = img.resize(tuple(size))
        res = np.asarray(img)

        for y in range(len(res)):
            for x, color in enumerate(res[y]):
                self.add([x + xIndex, y + yIndex, tuple(color)])

class TC_Sprite(BaseObject):
    def __init__(self, xIndex, yIndex, sprite):
        super().__init__()
        self.new(xIndex, yIndex, sprite)

    def new(self, xIndex, yIndex, sprite):
        if self.reset == True: self.data = []
        
        xIndex = roundInt(xIndex)
        yIndex = roundInt(yIndex)

        xCurrent = xIndex

        for x, y, color in sprite:
            self.add([x + xIndex, y + yIndex, color])



# ---------------
# Terminal canvas
# ---------------

class TCanvas():
    def __init__(self, width:int=None, height:int=None):
        if width == None and height == None:
            self.width, self.height = shutil.get_terminal_size()
            self.height *= 2
        else:
            self.width = width
            self.height = height

        self.totalPixels = self.width * self.height

        self.wCenter = self.width//2
        self.hCenter = self.height//2

        self.screenPixels = []
        self.screenBuffer = []

        self.xOff = 0
        self.yOff = 0

        self.backgroundColor = (255, 255, 255)

        print(SCREEN_CLEAR)
        self.clear()
        self.screenBuffer = self.screenPixels
        self.buffered = False


    # Display functions
    
    def putPixel(self, xIndex, yIndex, color=(0,0,0)):
        x = xIndex + self.xOff
        y = yIndex + self.yOff

        screen = self.screenPixels
        width = self.width
        
        if self.inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = screen[y*width + x]
                alpha = 1/255 * color[3]
                newColor = [
                    (alpha*color[i] + (1-alpha)*colorBelow[i])
                    for i in range(3)
                ]
                color = tuple(newColor)
                
            screen[y*width + x] = (
                roundInt(color[0]),
                roundInt(color[1]),
                roundInt(color[2])
            )

    def draw(self, object):
        putPixel = self.putPixel

        for pixel in object.data:
            putPixel(*pixel)

    def show(self, cursor=False):
        display = [CURSOR_HOME] if cursor else [CURSOR_HOME + CURSOR_HIDE]

        screen = self.screenPixels
        buffer = self.screenBuffer
        width = self.width
        hCenter = self.hCenter
        append = display.append
        sys_write = sys.stdout.write
        sys_flush = sys.stdout.flush

        fg = getFGColor
        bg = getBGColor

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

                if not self.buffered:
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

        append(COLOR_RESET)

        sys_write(''.join(display))
        sys_flush()

        self.screenBuffer = screen
        self.buffered = True

    def background(self, color, clear=True):
        self.backgroundColor = color
        if clear: self.clear()

    def clear(self):
        self.screenPixels = [
            self.backgroundColor for _ in range(self.totalPixels)
            ]

    def end(self):
        print(f"\033[{self.height}H" + CURSOR_SHOW)


    # Graphical objects

    def point(self, xIndex, yIndex, color=(0,0,0)):
        return TC_Point(xIndex, yIndex, color)

    def line(self, xStart, yStart, xEnd, yEnd, color=(0,0,0)):
        return TC_Line(xStart, yStart, xEnd, yEnd, color)

    def triangle(self, x1, y1, x2, y2, x3, y3, color=(0,0,0)):
        return TC_Triangle(x1, y1, x2, y2, x3, y3, color)

    def rectangle(self, xStart, yStart, xEnd, yEnd, mode="solid", color=(0,0,0)):
        return TC_Rectangle(xStart, yStart, xEnd, yEnd, mode, color)

    def ellipse(self, xStart, yStart, xEnd, yEnd, mode="solid", color=(0,0,0)):
        return TC_Ellipse(xStart, yStart, xEnd, yEnd, mode, color)

    def text(self, xIndex, yIndex, message, font=None, spacing=0, anchor_x="left", anchor_y="top", color=(0,0,0)):
        return TC_Text(xIndex, yIndex, message, font, spacing, anchor_x, anchor_y, color)

    def image(self, xIndex, yIndex, image_dir, size=None):
        return TC_Image(xIndex, yIndex, image_dir, size)

    def sprite(self, xIndex, yIndex, sprite):
        return TC_Sprite(xIndex, yIndex, sprite)
        
            
    # Canvas transformation
    
    def flip(self, direction:str=None):
        if direction in ["h", "horizontal", "y"]:
            self.screenPixels = [
                [self.screenPixels[y][self.width-x-1] for x in range(self.width)]
                for y in range(self.height)
                ]
        elif direction in ["v", "vertical", "x"]:
            self.screenPixels = [
                [self.screenPixels[self.height-y-1][x] for x in range(self.width)]
                for y in range(self.height)
                ]
        else:
            self.screenPixels = [
                [self.screenPixels[self.height-y-1][self.width-x-1] for x in range(self.width)]
                for y in range(self.height)
                ]

    def translate(self, xIndex, yIndex):
        self.xOff = int(xIndex)
        self.yOff = int(yIndex)


    # Save image

    def save(self, name=None, ext=".png", dir=""):
        if name is None:
            name = time.strftime("%Y_%m_%d %H_%M_%S", time.localtime())
            
        toNPArray = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        width = self.width
        height = self.height
        for y in range(height):
            for x in range(width):
                red, green, blue = self.screenPixels[y*width + x]
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
        
    def inRange(self, xIndex, yIndex, xRStart=None, xREnd=None, yRStart=None, yREnd=None):
        if not xRStart: xRStart = 0
        if not xREnd: xREnd = self.width
        if not yRStart: yRStart = 0
        if not yREnd: yREnd = self.height
        return xIndex in range(xRStart, xREnd) and yIndex in range(yRStart, yREnd)

# ----------------------------
# Terminal canvas, 3D pipeline
# ----------------------------

class TCanvas3D(TCanvas):
    def __init__(self):
        super().__init__()

        self.depthIntensity = 0
        
        self.resetDepthBuffer()
        
        
    # Display functions
    
    def putPixel(self, xIndex, yIndex, color=(0,0,0), zIndex=None):
        x = xIndex + self.xOff
        y = yIndex + self.yOff

        if len(color) < 3:
            raise Exception("Missing color arguments. Must be an iterable with RGB values.")
        
        if self.inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = self.screenPixels[y*self.width + x]
                alpha = 1/255 * color[3]
                newColor = [
                    alpha*color[i] + (1-alpha)*colorBelow[i]
                    for i in range(3)
                ]
                color = tuple(newColor)
                
            if zIndex is not None:
                if zIndex < self.depthBuffer[y, x]:
                    self.depthBuffer[y, x] = zIndex
                    self.screenPixels[y*self.width + x] = (
                        roundInt(color[0] * (1 - self.depthIntensity * zIndex)),
                        roundInt(color[1] * (1 - self.depthIntensity * zIndex)),
                        roundInt(color[2] * (1 - self.depthIntensity * zIndex))
                    )
            else:
                self.screenPixels[y*self.width + x] = (
                    roundInt(color[0]),
                    roundInt(color[1]),
                    roundInt(color[2])
                )
                
    def resetDepthBuffer(self):
        self.depthBuffer = np.full((self.height, self.width), np.inf)

    # Graphical objects

    def triangle3D(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, color=(0,0,0)):
        return TC_Triangle3D(x1, y1, z1, x2, y2, z2, x3, y3, z3, color)