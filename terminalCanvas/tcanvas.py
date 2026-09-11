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
    """
    Bound all input RGB values to a specific range of [0, 255].

    Parameters:
    - color: tuple[int, int, int]

    Returns:
    - tuple[int, int, int]
    """

    red = max(min(objects.roundInt(color[0]), 255), 0)
    green = max(min(objects.roundInt(color[1]), 255), 0)
    blue = max(min(objects.roundInt(color[2]), 255), 0)

    return red, green, blue

def _getFGColor(color: tuple[int, int, int]) -> str:
    """
    Returns the ANSI escape sequence for changing the foreground color.

    Parameters:
    - color: tuple[int, int, int]

    Returns:
    - str
    """

    if color is None: return "\033[38;2;0;0;0m"

    red, green, blue = _sanitizeColor(color)
    return f"\033[38;2;{red};{green};{blue}m"

def _getBGColor(color: tuple[int, int, int]) -> str:
    """
    Returns the ANSI escape sequence for changing the background color.

    Parameters:
    - color: tuple[int, int, int]

    Returns:
    - str
    """

    if color is None: return "\033[48;2;0;0;0m"

    red, green, blue = _sanitizeColor(color)
    return f"\033[48;2;{red};{green};{blue}m"

def _combineAlpha(
        c_top: tuple[int, int, int, int],
        c_bot: tuple[int, int, int]
) -> tuple[int, int, int]:
    """
    Returns the RGB color formed by blending two colors, one of which is translucent (alpha < 255).

    `c_top` should be the color laying above `c_bot` and should have an additional value for alpha.

    Parameters:
    - c_top: tuple[int, int, int, int]
    - c_bot: tuple[int, int, int]

    Returns:
    - tuple[int, int, int]
    """

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
    """
    The main terminalCanvas class for drawing and displaying the canvas.

    `TCanvas` mainly supports 2D rendering, but 3D is also supported (though very limited).

    To make a canvas, create a new instance of `TCanvas`:
    `canvas = terminalCanvas.TCanvas()`

    Then, you can use these methods to perform certain actions with the canvas:
    - `canvas.show()` to show the canvas on the terminal
    - `canvas.draw()` to draw one of terminalCanvas's object classes such as `Line` or `Triangle`
    - `canvas.clear()` to clear the canvas
    - `canvas.background((R, G, B))` to set a background color
    - `canvas.end()` to properly reset the color modes of the terminal

    There are also certain attributes you can either access or modify:
    - `canvas.width` and `canvas.height`, the canvas resolution
    - `canvas.wCenter` and `canvas.hCenter`, half of the canvas' width and height respectively
    - `canvas.depthIntensity`, the depth intensity for 3D objects. The higher the number, the darker high-z objects are
    """

    def __init__(
            self,
            width: int = None, 
            height: int = None,
    ) -> None:
        """
        Initialises `TCanvas`.

        Parameters:
        - width: int = None
        - height: int = None

        Returns:
        - None
        """

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
        """
        Plots a pixel to `_screenPixels`, a.k.a. the canvas.

        `xIndex`, `yIndex`, and `color` are absolutely necessary since they define where and how to plot the pixel.
        The pixel color can be RGB or RGBA.

        `zIndex` is mainly for layered / 3D rendering and is optional.

        Parameters:
        - xIndex: int
        - yIndex: int
        - color: tuple[int, int, int, int] = (0, 0, 0, 255)
        - zIndex: float = None

        Returns:
        - None
        """

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
        """
        Draws the object on the canvas.
        More specifically, this method puts all the pixel data from the object into a helper method that can process these pixels and put them on the canvas.

        `object` must be an instance of one of the few classes that define shapes, text and images, such as `Line` or `Triangle`.

        Parameters:
        - object

        Returns:
        - None
        """

        plot = self._plot

        for pixel in object.data:
            plot(*pixel)

    def show(self, cursor: bool = False, lock_to_terminal: bool = False) -> None:
        """
        Displays the canvas onto the terminal.

        `cursor` shows the cursor while printing to the terminal. By default, this is set to False. This is purely visual and does not affect performance.

        `lock_to_terminal` limits the canvas resolution to the current terminal resolution.
        This is particularly useful if the canvas resolution is bigger than that of the terminal.
        By default, this is set to False.

        Parameters:
        - cursor: bool = False
        - lock_to_terminal: bool = False

        Returns:
        - None
        """

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

    def background(self, color: tuple[int, int, int], clear: bool = True) -> None:
        """
        Sets an RGB color to the background.

        `clear` runs the `clear()` method, which effectively fills the entire canvas with the background color.
        This is set to True by default.

        Parameters:
        - color: tuple[int, int, int]
        - clear = True

        Returns:
        - None
        """

        self._bgColor = color
        if clear:
            self.clear()

    def clear(self) -> None:
        """
        Clears the canvas. More specifically, it fills the entire canvas with the current background color.
        """

        self._screenPixels = [
            self._bgColor for _ in range(self.totalPixels)
            ]
        self.resetDepthBuffer()

    def end(self, clear_all: bool = False) -> None:
        """
        Allows the terminal to return to its regular state. Particularly useful after using `show()` or after an exception.
        More specifically, it prints out a few ANSI escape sequences to hopefully reset the color modes and cursor visibility state.

        `clear_all` clears the entire screen if set to True. By default, it is set to False, which leaves the entire canvas above the command line.

        Parameters:
        - clear_all: bool = False

        Returns:
        - None
        """

        print(f"\033[{self.height}H" + _CURSOR_SHOW + (_SCREEN_CLEAR if clear_all else ''))

    def space(self) -> tuple[int, int]:
        """
        A generator that returns every (x, y) coordinate of the canvas that is currently visible.

        This implementation of `space()` iterates through every value of x before iterating to the next value of y.
        """

        xMin, xMax = 0 - self._xOff, self.width - self._xOff
        yMin, yMax = 0 - self._yOff, self.height - self._yOff
        for y in range(yMin, yMax):
            for x in range(xMin, xMax):
                yield (x, y)

    def resize(self, width: int = None, height: int = None) -> None:
        """
        Resizes the canvas to the terminal resolution, or to a specific one.

        When either `width` or `height` is set to None, the width and height of the terminal will be used instead.

        Parameters:
        - width: int = None
        - height: int = None

        Returns:
        - None
        """

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
        """
        Resets the depth buffer of the canvas. Particularly useful with 3D objects.

        This is called automatically by `clear()`.
        Unless there's a specific circumstance where you need to reset the buffer midway through drawing, you don't need to call this method at all.
        """

        self.depthBuffer = np.full((self.height, self.width), np.inf)
        
            
    # Canvas transformation
    
    def flip(self, direction: str = None) -> None:
        """
        Flips the canvas either horizontally, vertically, or both.

        `direction` can be either:
        - `h`: flips the canvas horizontally
        - `v`: flips the canvas vertically
        - None or anything else: flips the canvas horizontally AND vertically, or rotates the canvas 180°

        Parameters:
        - direction: str = None

        Returns:
        - None
        """

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

    def translate(self, xIndex: int, yIndex: int) -> None:
        """
        Translates the canvas or shifts the origin (0, 0) to a new point.

        By default, the origin is on the top left.
        Every time you put the coordinate of a point or vertice at (0, 0), it will be at the top left.

        Translating the canvas to something like (canvas.wCenter, canvas.hCenter) will move the origin to that center,
        and putting the coordinate of a point or vertice at (0, 0) will now make it appear at the center instead.

        This method is "destructive", not "additive". It replaces the shifting, not add to it.

        Parameters:
        - xIndex: int
        - yIndex: int

        Returns:
        - None
        """

        self._xOff = int(xIndex)
        self._yOff = int(yIndex)


    # Save image

    def save(self, dir: str, scale: int = None) -> None:
        """
        Saves the canvas as an image.

        `dir` is the directory of the image, and can be relative or absolute.

        `scale` is the integer scale of the output image. For example, `scale = 2` makes the image twice as big.
        By default, it is set to None, which ignores scaling entirely.

        Parameters:
        - dir: str
        - scale: int = None

        Returns:
        - None
        """

        toNPArray = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        width = self.width
        height = self.height
        for y in range(height):
            for x in range(width):
                red, green, blue = self._screenPixels[y*width + x]
                alpha = 255
                toNPArray[y, x] = np.array([red, green, blue, alpha])

        newImage = Image.fromarray(toNPArray)
        if scale is not None:
            newImage = newImage.resize(
                (newImage.width * scale, newImage.height * scale),
                Image.Resampling.NEAREST
                )
        newImage.save(dir)

    
    # Keyboard & mouse input

    def _keyPressed_WINDOWS(self, key: str, hold: bool = True) -> bool:
        """
        Returns the pressed state of a key, designated for Windows systems.

        Refer to `keyPressed()` for the full description.
        """

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
        """
        Returns the pressed state of a key, designated for Unix systems.

        This is purely a fallback system. I cannot guarantee that this works.

        Refer to `keyPressed()` for the full description.
        """
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
        """
        Returns the pressed state of a key.

        `key` is the set alias for the target key to detect. It should be in all caps.
        You can check out `terminalCanvas.vk.VK_WINDOWS` (dict) for the full list of aliases to use.
        (VK_UNIX for available keys for Unix systems)

        `hold` detects the pressed state for a specific key every single call.
        If set to False, it will only return True once for the first time it detects that key being pressed,
        then it will return False until the key has been released.
        By default, it is set to True, which will always return True if it detects the key is being pressed.
        Basically, `hold = False` is instantaneous and temporary, while `hold = True` is persistent.

        Parameters:
        - key: str
        - hold: bool = True

        Returns:
        - bool
        """

        if input_mode == "Windows":
            return self._keyPressed_WINDOWS(key=key, hold=hold)
        elif input_mode == "Unix":
            return self._keyPressed_UNIX(key=key, hold=hold)

    def getMousePos(self) -> tuple[int, int] | None:
        """
        Returns the coordinate of the mouse on the canvas.

        The coordinate can be negative, meaning the mouse is outside the terminal window.

        This method can only be used on Windows systems. There is no solution for Unix.

        Parameters:
        - None

        Returns:
        - tuple[int, int]
        - None
        """

        if input_mode == "Unix":
            raise OSError("Cannot use getMousePos() on non-Windows system/terminal.")

        point = _point_t()
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
        mx = (point.x - origin.x) / (client.right // self.width)
        my = (point.y - origin.y) / (client.bottom // self.height)

        return int(mx), int(my)


    # Other functions        
        
    def _inRange(
            self,
            xIndex: int, yIndex: int, 
            xStart: int = 0, xEnd: int = None,
            yStart: int = 0, yEnd: int = None
    ) -> bool:
        """
        Checks if a pixel is inside the visible boundary of the canvas.

        Parameters:
        - xIndex: int
        - yIndex: int
        - xStart: int = 0
        - xEnd: int = None
        - yStart: int = 0
        - yEnd: int = None

        Returns:
        - bool
        """

        if xEnd is None: xEnd = self.width
        if yEnd is None: yEnd = self.height
        return xStart <= xIndex < xEnd and yStart <= yIndex < yEnd


# -------------------------------
# Terminal canvas, 2D, UI-focused
# -------------------------------

class TCanvasUI(TCanvas):
    """
    The terminalCanvas class designated for user interfaces.

    To make a canvas, create a new instance of `TCanvasUI`:
    `canvas = terminalCanvas.TCanvasUI()`

    Then, you can use these methods to perform certain actions with the canvas:
    - `canvas.show()` to show the canvas on the terminal
    - `canvas.draw()` to draw one of terminalCanvas's UI object classes such as `RectangleUI` or `TextUI`
    - `canvas.clear()` to clear the canvas
    - `canvas.background((R, G, B))` to set a background color
    - `canvas.end()` to properly reset the color modes of the terminal

    You can still draw non-UI objects on `TCanvasUI`, but they will be stretched vertically,
    due to difference in the `show()` method between `TCanvas` and `TCanvasUI`.

    There are also certain attributes you can either access or modify:
    - `canvas.width` and `canvas.height`, the canvas resolution
    - `canvas.wCenter` and `canvas.hCenter`, half of the canvas' width and height respectively
    """

    def __init__(
            self,
            width: int = None, 
            height: int = None,
    ) -> None:
        """
        Initialises `TCanvasUI`.

        Parameters:
        - width: int = None
        - height: int = None

        Returns:
        - None
        """
        
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
        """
        Plots a pixel to `_screenPixels`, a.k.a. the canvas.

        `xIndex`, `yIndex`, and `color` are absolutely necessary since they define where and how to plot the pixel.
        The pixel color can be RGB or RGBA.

        `char` is the character to use.
        
        `bgcolor` is the background color.

        Parameters:
        - xIndex: int
        - yIndex: int
        - color: tuple[int, int, int, int] = (0, 0, 0, 255)
        - char: str = "█"
        - bgcolor: tuple[int, int, int, int] = None

        Returns:
        - None
        """

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
        """
        Displays the canvas onto the terminal.

        `cursor` shows the cursor while printing to the terminal. By default, this is set to False. This is purely visual and does not affect performance.

        `lock_to_terminal` limits the canvas resolution to the current terminal resolution.
        This is particularly useful if the canvas resolution is bigger than that of the terminal.
        By default, this is set to False.

        Parameters:
        - cursor: bool = False
        - lock_to_terminal: bool = False

        Returns:
        - None
        """

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
        """
        Clears the canvas. More specifically, it fills the entire canvas with the current background color.
        """

        self._screenPixels = [
            self._bgColor + (' ',) + self._bgColor for _ in range(self.totalPixels)
            ]

    def resize(self, width: int = None, height: int = None) -> None:
        """
        Resizes the canvas to the terminal resolution, or to a specific one.

        When either `width` or `height` is set to None, the width and height of the terminal will be used instead.

        Parameters:
        - width: int = None
        - height: int = None

        Returns:
        - None
        """

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