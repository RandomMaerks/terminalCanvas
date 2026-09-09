import os
import time
import sys
import shutil
try:
    # Import ctypes, mainly for user input on Windows
    import ctypes
    from ctypes import wintypes
    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    input_mode = "Windows"
except AttributeError:
    # Fallback to termios, "should" work on UNIX
    import termios, fcntl
    input_mode = "Unix"

from PIL import Image
import numpy as np

from . import objects
from .vk import VK_WINDOWS, VK_UNIX

os.system("")

# ---------------------
# ANSI escape sequences
# ---------------------

_COLOR_RESET = "\033[0m"
_CURSOR_HOME = "\033[H"
_CURSOR_SHOW = "\033[?25h"
_CURSOR_HIDE = "\033[?25l"
_SCREEN_CLEAR = "\033[2J"

# ----------------------------
# Predefined display functions
# ----------------------------

def _sanitizeColor(color: tuple[int, int, int]) -> tuple[int, int, int]:
    red = max(min(objects.roundInt(color[0]), 255), 0)
    green = max(min(objects.roundInt(color[1]), 255), 0)
    blue = max(min(objects.roundInt(color[2]), 255), 0)

    return red, green, blue

def _getFGColor(color: tuple[int, int, int]) -> str:
    if color is None: return "\033[38;2;0;0;0m"

    red, green, blue = _sanitizeColor(color)
    return f"\033[38;2;{red};{green};{blue}m"

def _getBGColor(color: tuple[int, int, int]) -> str:
    if color is None: return "\033[48;2;0;0;0m"

    red, green, blue = _sanitizeColor(color)
    return f"\033[48;2;{red};{green};{blue}m"

def _combineAlpha(
        c_top: tuple[int, int, int, int],
        c_bot: tuple[int, int, int]
) -> tuple[int, int, int]:
    alpha = 1/255 * c_top[3]
    c_combined = [
        (alpha*c_top[i] + (1-alpha)*c_bot[i])
        for i in range(3)
    ]
    return tuple(c_combined)

# ------------------
# Extraneous classes
# ------------------

class _point_t(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_long),
        ('y', ctypes.c_long)
    ]

# ---------------
# Terminal canvas
# ---------------

class TCanvas:
    def __init__(
            self,
            width: int = None, 
            height: int = None,
    ) -> None:

        if width is None:
            self.width, _ = shutil.get_terminal_size()
        else:
            self.width = width

        if height is None:
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

        self.clear()
        self._screenBuffer = self._screenPixels
        self._buffered = False

        self.depthIntensity = 0

        self._lastKeyPressed = {}


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
        roundInt = objects.roundInt

        if len(color) < 3:
            raise Exception("Missing color arguments. Must be an iterable with RGB values.")
        
        if self._inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = self._screenPixels[y*width + x]
                color = _combineAlpha(color, colorBelow)
                
            if zIndex is not None:
                if zIndex < self.depthBuffer[y, x]:
                    self.depthBuffer[y, x] = zIndex
                    self._screenPixels[y*width + x] = (
                        roundInt(color[0] * (1 - depthIntensity * zIndex)),
                        roundInt(color[1] * (1 - depthIntensity * zIndex)),
                        roundInt(color[2] * (1 - depthIntensity * zIndex))
                    )
            else:
                self._screenPixels[y*width + x] = (
                    roundInt(color[0]),
                    roundInt(color[1]),
                    roundInt(color[2])
                )

    def draw(self, object) -> None:
        plot = self._plot

        for pixel in object.data:
            plot(*pixel)

    def show(self, cursor = False, lock_to_terminal: bool = False) -> None:
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

        if lock_to_terminal:
            xRange, yRange = shutil.get_terminal_size()
            xRange = min(width, xRange)
            yRange = min(hCenter, (yRange // 2) * 2 - 1)
        else:
            xRange, yRange = width, hCenter

        for y in range(yRange):
            yIndex = y*2
            row1 = yIndex * width
            row2 = row1 + width

            for x in range(xRange):
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
        self.resetDepthBuffer()

    def end(self, clear_all: bool = False) -> None:
        print(f"\033[{self.height}H" + _CURSOR_SHOW + (_SCREEN_CLEAR if clear_all else ''))

    def space(self) -> tuple[int, int]:
        xMin, xMax = 0 - self._xOff, self.width - self._xOff
        yMin, yMax = 0 - self._yOff, self.height - self._yOff
        for y in range(yMin, yMax):
            for x in range(xMin, xMax):
                yield (x, y)

    def resize(self, width: int = None, height: int = None) -> None:
        if width is None: tempwidth, _ = shutil.get_terminal_size()
        else: tempwidth = width
        self.width = tempwidth

        if height is None: _, tempheight = shutil.get_terminal_size()
        else: tempheight = height
        self.height = tempheight * 2

        self.totalPixels = self.width * self.height

        self.wCenter = self.width//2
        self.hCenter = self.height//2

        self._screenPixels = []
        self.clear()
        self._screenBuffer = self._screenPixels

        self._buffered = False

    def resetDepthBuffer(self) -> None:
        self.depthBuffer = np.full((self.height, self.width), np.inf)
        
            
    # Canvas transformation
    
    def flip(self, direction: str = None) -> None:
        width = self.width
        height = self.height

        if direction in {"h"}:
            self._screenPixels = [
                self._screenPixels[y*width + x] 
                for y in range(height)                
                for x in reversed(range(width))
                ]
        elif direction in {"v"}:
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

    def _keyPressed_WINDOWS(self, key: str, hold: bool = True) -> bool:
        map = VK_WINDOWS

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

    def _keyPressed_UNIX(self, key: str, hold: bool = True) -> bool:
        # Test function. Fallback for Linux terminals. No guarantee that it actually works
        map = VK_UNIX

        if key in map:
            vk = map[key]
        elif len(key) == 1:
            vk = key.lower()
        else:
            raise KeyError(f"Key {key} has not been defined in selected map.")
            
        fd = sys.stdin.fileno()

        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] &= ~(termios.ICANON | termios.ECHO)
        termios.tcsetattr(fd, termios.TCSANOW, new)

        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

        try:
            try:
                data = os.read(fd, 8).decode(errors="ignore")
            except (IOError, BlockingIOError):
                data = ""
                
            current = (data == vk)
            previous = self._lastKeyPressed.get(vk, False)

            self._lastKeyPressed[vk] = current

            if hold is True:
                return current
            else:
                return current and not previous
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

    def keyPressed(self, key: str, hold: bool = True) -> bool:
        if input_mode == "Windows":
            return self._keyPressed_WINDOWS(key=key, hold=hold)
        elif input_mode == "Unix":
            return self._keyPressed_UNIX(key=key, hold=hold)

    def getMousePos(self) -> tuple[int, int] | None:
        if input_mode == "Unix":
            raise OSError("Cannot use getMousePos() on non-Windows system/terminal.")

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


# -------------------------------
# Terminal canvas, 2D, UI-focused
# -------------------------------

class TCanvasUI(TCanvas):
    def __init__(
            self,
            width: int = None, 
            height: int = None,
    ) -> None:

        if width is None:
            self.width, _ = shutil.get_terminal_size()
        else:
            self.width = width

        if height is None:
            _, self.height = shutil.get_terminal_size()
        else:
            self.height = height

        self.totalPixels = self.width * self.height

        self.wCenter = self.width//2
        self.hCenter = self.height//2

        self._screenPixels = []
        self._screenBuffer = []

        self._xOff = 0
        self._yOff = 0

        self._bgColor = (0, 0, 0)

        #print(_SCREEN_CLEAR)
        self.clear()
        self._screenBuffer = self._screenPixels
        self._buffered = False

        self._lastKeyPressed = {}


    # Display functions

    def _plot(
            self,
            xIndex: int, yIndex: int, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            char: str = "█",
            bgcolor: tuple[int, int, int, int] = None,
    ) -> None:
        x = xIndex + self._xOff
        y = yIndex + self._yOff

        width = self.width
        roundInt = objects.roundInt

        if bgcolor is None: bgcolor = color
        
        if self._inRange(x, y):
            if len(color) == 4 and color[3] != 255:
                colorBelow = self._screenPixels[y*width + x][0:3]
                color = _combineAlpha(color, colorBelow)

            if len(bgcolor) == 4 and bgcolor[3] != 255:
                bgcolorBelow = self._screenPixels[y*width + x][4:7]
                bgcolor = _combineAlpha(bgcolor, bgcolorBelow)
                
            self._screenPixels[y*width + x] = (
                roundInt(color[0]),
                roundInt(color[1]),
                roundInt(color[2]),
                char,
                roundInt(bgcolor[0]),
                roundInt(bgcolor[1]),
                roundInt(bgcolor[2]),
            )

    def show(self, cursor = False, lock_to_terminal: bool = False) -> None:
        display = [_CURSOR_HOME] if cursor else [_CURSOR_HOME + _CURSOR_HIDE]

        width = self.width
        height = self.height
        append = display.append
        sys_write = sys.stdout.write
        sys_flush = sys.stdout.flush

        fg = _getFGColor
        bg = _getBGColor

        last_p1 = None
        last_bgp1 = None

        if lock_to_terminal:
            xRange, yRange = shutil.get_terminal_size()
            xRange = min(width, xRange)
            yRange = min(height, (yRange // 2) * 2 - 1)
        else:
            xRange, yRange = width, height

        for y in range(yRange):
            row1 = y * width

            if lock_to_terminal and y >= term_height: break

            for x in range(xRange):
                if lock_to_terminal and x >= term_width: break

                i1 = row1 + x

                dp1 = self._screenPixels[i1]
                db1 = self._screenBuffer[i1]

                p1 = dp1[:3]
                b1 = db1[:3]

                bgp1 = dp1[4:7]
                bgb1 = db1[4:7]

                cp1 = dp1[3]
                cb1 = db1[3]

                if not self._buffered:
                    if bgp1 != last_bgp1 or y == 0:
                        append(bg(bgp1))
                    if p1 != last_p1 or y == 0:
                        append(fg(p1))
                    append(cp1)

                    last_p1 = p1
                    last_bgp1 = bgp1
                else:
                    if p1 != b1 or bgp1 != bgb1 or cp1 != cb1:
                        append(f"\033[{y+1};{x+1}H")
                        append(bg(bgp1))
                        append(fg(p1))
                        append(cp1)

            if y < height-1: append("\n")

        append(_COLOR_RESET)

        sys_write(''.join(display))
        sys_flush()

        self._screenBuffer = list(self._screenPixels)
        self._buffered = True

    def clear(self) -> None:
        self._screenPixels = [
            self._bgColor + (' ',) + self._bgColor for _ in range(self.totalPixels)
            ]

    def resize(self, width: int = None, height: int = None) -> None:
        if width is None: tempwidth, _ = shutil.get_terminal_size()
        else: tempwidth = width
        self.width = tempwidth

        if height is None: _, tempheight = shutil.get_terminal_size()
        else: tempheight = height
        self.height = tempheight

        self.totalPixels = self.width * self.height

        self.wCenter = self.width//2
        self.hCenter = self.height//2

        self._screenPixels = []
        self.clear()
        self._screenBuffer = self._screenPixels

        self._buffered = False