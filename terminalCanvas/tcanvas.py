from __future__ import annotations

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
from .helper import *

os.system("")

# ---------------------
# ANSI escape sequences
# ---------------------

_COLOR_RESET = "\033[0m"
_CURSOR_HOME = "\033[H"
_CURSOR_SHOW = "\033[?25h"
_CURSOR_HIDE = "\033[?25l"
_SCREEN_CLEAR = "\033[2J"

# ------------------
# Extraneous classes
# ------------------

class _point_t(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_long),
        ('y', ctypes.c_long)
    ]

# ----------------------------
# Predefined display functions
# ----------------------------

def _sanitize_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """
    Bound all input RGB values to a specific range of [0, 255].

    Parameters:
    - color: tuple[int, int, int]

    Returns:
    - tuple[int, int, int]
    """

    red = clamp(round_int(color[0]), 0, 255)
    green = clamp(round_int(color[1]), 0, 255)
    blue = clamp(round_int(color[2]), 0, 255)

    return red, green, blue

def _get_foreground_color(color: tuple[int, int, int]) -> str:
    """
    Returns the ANSI escape sequence for changing the foreground color.

    Parameters:
    - color: tuple[int, int, int]

    Returns:
    - str
    """

    if color is None: return "\033[38;2;0;0;0m"

    red, green, blue = _sanitize_color(color)
    return f"\033[38;2;{red};{green};{blue}m"

def _get_background_color(color: tuple[int, int, int]) -> str:
    """
    Returns the ANSI escape sequence for changing the background color.

    Parameters:
    - color: tuple[int, int, int]

    Returns:
    - str
    """

    if color is None: return "\033[48;2;0;0;0m"

    red, green, blue = _sanitize_color(color)
    return f"\033[48;2;{red};{green};{blue}m"

def _combine_alpha(
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
    - `canvas.width_center` and `canvas.height_center`, half of the canvas' width and height respectively
    - `canvas.depth_intensity`, the depth intensity for 3D objects. The higher the number, the darker high-z objects are
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

        tw, th = shutil.get_terminal_size()
        self.width = tw if width is None else width
        self.height = th * 2 if height is None else height

        self.total_pixels = self.width * self.height

        self.width_center = self.width // 2
        self.height_center = self.height // 2

        self._screen_pixels = []
        self._screen_buffer = []

        self._x_off = 0
        self._y_off = 0

        self.background_color = (255, 255, 255)

        self.clear()
        self._screen_buffer = self._screen_pixels
        self._buffered = False

        self.depth_intensity = 0
        self.depth_accuracy = 4

        self._last_key_pressed = {}


    # Display functions

    def _plot(
            self,
            x: int, y: int, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255), 
            z: float = None
    ) -> None:
        """
        Plots a pixel to `_screen_pixels`, a.k.a. the canvas.

        `x`, `y`, and `color` are absolutely necessary since they define where and how to plot the pixel.
        The pixel color can be RGB or RGBA.

        `z` is mainly for layered / 3D rendering and is optional.

        Parameters:
        - x: int
        - y: int
        - color: tuple[int, int, int, int] = (0, 0, 0, 255)
        - z: float = None

        Returns:
        - None
        """

        x += self._x_off
        y += self._y_off

        width = self.width
        depth_intensity = self.depth_intensity
        depth_accuracy = self.depth_accuracy

        if len(color) < 3:
            raise Exception("Missing color arguments. Must be an iterable with RGB values.")
        
        if self._in_range(x, y):
            index = y * width + x

            if len(color) == 4 and color[3] != 255:
                color_below = self._screen_pixels[index]
                color = _combine_alpha(color, color_below)
                
            if z is not None:
                if z < self.depth_buffer[index]:
                    mult = round(1 - depth_intensity * z, depth_accuracy)
                    self.depth_buffer[index] = z
                    self._screen_pixels[index] = tuple(
                        round_int(color[i] * mult)
                        for i in range(3)
                    )
            else:
                self._screen_pixels[index] = tuple(
                    round_int(color[i])
                    for i in range(3)
                )

    def draw(
            self,
            object: BaseObject | BaseCompoundObject,
            camera: Camera | None = None
    ) -> None:
        """
        Draws the object on the canvas.
        More specifically, this method puts all the pixel data from the object into a helper method that can process these pixels and put them on the canvas.

        `object` must be an instance of one of the few classes that define shapes, text and images, such as `Line` or `Triangle`.

        You can also put a camera for 3D objects. Objects will be translated into the 3D space and projected onto the camera.

        Parameters:
        - object: BaseObject | BaseCompoundObject
        - camera: Camera | None = None

        Returns:
        - None
        """

        # In case of a compound object: draw its components
        if getattr(object, '_compound', False):
            if object._modified:
                object._build()
                object._modified = False

            for child_object in object.objects:
                self.draw(child_object, camera)

            return

        # In case that a camera is passed through: translate the object through camera view
        if camera is not None:
            camera._draw(object, self)

            return

        # In case of all graphical objects: regular draw
        plot = self._plot

        if object._modified:
            object._build()
            object._modified = False

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

        display = [
            _CURSOR_HOME +
            (_CURSOR_HIDE if not cursor else '')
        ]

        width = self.width
        height_center = self.height_center
        append = display.append
        sys_write = sys.stdout.write
        sys_flush = sys.stdout.flush

        fg = _get_foreground_color
        bg = _get_background_color

        last_p1 = None
        last_p2 = None

        if lock_to_terminal:
            x_range, y_range = shutil.get_terminal_size()
            x_range = min(width, x_range)
            y_range = min(height_center, (y_range // 2) * 2 - 1)
        else:
            x_range, y_range = width, height_center

        for y in range(y_range):
            yIndex = y * 2
            row1 = yIndex * width
            row2 = row1 + width

            for x in range(x_range):
                i1 = row1 + x
                i2 = row2 + x

                p1 = self._screen_pixels[i1]
                p2 = self._screen_pixels[i2]

                b1 = self._screen_buffer[i1]
                b2 = self._screen_buffer[i2]

                if not self._buffered:
                    if p1 != last_p1 or p2 != last_p2 or y == 0:
                        append(bg(p2) + fg(p1))
                    append("▀")

                    last_p1 = p1
                    last_p2 = p2
                else:
                    if p1 != b1 or p2 != b2:
                        append(f"\033[{y+1};{x+1}H")

                        if p1 == p2:
                            if p2 != last_p2:
                                append(bg(p2))
                            append(" ")
                        else:
                            if p1 != last_p1 or p2 != last_p2:
                                append(bg(p2) + fg(p1))
                            append("▀")

                        last_p1 = p1
                        last_p2 = p2

            if y < height_center-1: append("\n")

        append(_COLOR_RESET)

        sys_write(''.join(display))
        sys_flush()

        self._screen_buffer = list(self._screen_pixels)
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

        self.background_color = color
        if clear:
            self.clear()

    def clear(self) -> None:
        """
        Clears the canvas. More specifically, it fills the entire canvas with the current background color.
        """

        self._screen_pixels = [self.background_color] * self.total_pixels
        self.reset_depth_buffer()

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

        xMin, xMax = 0 - self._x_off, self.width - self._x_off
        yMin, yMax = 0 - self._y_off, self.height - self._y_off
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

        tw, th = shutil.get_terminal_size()
        self.width = tw if width is None else width
        self.height = th * 2 if height is None else height

        self.total_pixels = self.width * self.height

        self.width_center = self.width//2
        self.height_center = self.height//2

        self._screen_pixels = []
        self.clear()
        self._screen_buffer = self._screen_pixels

        self._buffered = False

    def reset_depth_buffer(self) -> None:
        """
        Resets the depth buffer of the canvas. Particularly useful with 3D objects.

        This is called automatically by `clear()`.
        Unless there's a specific circumstance where you need to reset the buffer midway through drawing, you don't need to call this method at all.
        """

        self.depth_buffer = np.full((self.total_pixels), np.inf)
        
            
    # Transformation & image processing
    
    def flip(self, direction: str = None) -> None:
        """
        Flips the canvas either horizontally, vertically, or both.

        `direction` can be either:
        - `h`, `horizontal`: flips the canvas horizontally
        - `v`, `vertical`: flips the canvas vertically
        - None or anything else: flips the canvas horizontally AND vertically, or rotates the canvas 180°

        Parameters:
        - direction: str = None

        Returns:
        - None
        """

        width = self.width
        height = self.height

        if direction in {"h", "horizontal"}:
            self._screen_pixels = [
                self._screen_pixels[y*width + x] 
                for y in range(height)                
                for x in reversed(range(width))
                ]
        elif direction in {"v", "vertical"}:
            self._screen_pixels = [
                self._screen_pixels[y*width + x]
                for y in reversed(range(height))
                for x in range(width)
                ]
        else:
            self._screen_pixels = [
                self._screen_pixels[y*width + x]
                for y in reversed(range(height))
                for x in reversed(range(width))
                ]

    def translate(self, xIndex: int, yIndex: int) -> None:
        """
        Translates the canvas or shifts the origin (0, 0) to a new point.

        By default, the origin is on the top left.
        Every time you put the coordinate of a point or vertice at (0, 0), it will be at the top left.

        Translating the canvas to something like (canvas.width_center, canvas.height_center) will move the origin to that center,
        and putting the coordinate of a point or vertice at (0, 0) will now make it appear at the center instead.

        This method is "destructive", not "additive". It replaces the shifting, not add to it.

        Parameters:
        - xIndex: int
        - yIndex: int

        Returns:
        - None
        """

        self._x_off = int(xIndex)
        self._y_off = int(yIndex)

    def invert(
            self,
            x1: int = 0, y1: int = 0,
            x2: int = None, y2: int = None,
    ) -> None:
        """
        Inverts the colors of the canvas.

        You can set a specific region to invert using two points (x1, y1) and (x2, y2).
        By default, (x1, y1) is (0, 0), and (x2, y2) is (None, None), which then becomes
        (canvas.width - 1, canvas.height - 1), essentially the whole canvas.

        Parameters:
        - x1: int = 0
        - y1: int = 0
        - x2: int = None
        - y2: int = None

        Returns:
        - None
        """

        if x2 is None: x2 = self.width
        if y2 is None: y2 = self.height

        width = self.width

        for x, y in self.space():
            if not self._in_range(x, y, x1, x2, y1, y2):
                continue

            r, g, b = self._screen_pixels[y*width + x]
            self._screen_pixels[y*width + x] = (255 - r, 255 - g, 255 - b)

        self._buffered = False

    def blur(
            self,
            x1: int = 0, y1: int = 0,
            x2: int = None, y2: int = None,
            radius: int = 1,
    ) -> None:
        """
        Applies a box blur effect on the canvas.

        You can set a specific region to invert using two points (x1, y1) and (x2, y2).
        By default, (x1, y1) is (0, 0), and (x2, y2) is (None, None), which then becomes
        (canvas.width - 1, canvas.height - 1), essentially the whole canvas.

        Parameters:
        - x1: int = 0
        - y1: int = 0
        - x2: int = None
        - y2: int = None
        - radius: int = 1

        Returns:
        - None
        """

        if x2 is None: x2 = self.width
        if y2 is None: y2 = self.height

        width = self.width
        height = self.height

        new = [None] * self.total_pixels

        pixel_count = (radius * 2 + 1) * 2

        for x, y in self.space():
            if not self._in_range(x, y, x1, x2, y1, y2):
                new[y*width + x] = self._screen_pixels[y*width + x]
                continue

            all_r = 0
            all_g = 0
            all_b = 0

            for dy in range(y - radius, y + radius + 1):
                r, g, b = self._screen_pixels[
                    clamp(dy, 0, height - 1) *
                    width +
                    clamp(x, 0, width - 1)
                ]
                all_r += r
                all_g += g
                all_b += b

            for dx in range(x - radius, x + radius + 1):
                r, g, b = self._screen_pixels[
                    clamp(y, 0, height - 1) *
                    width +
                    clamp(dx, 0, width - 1)
                ]
                all_r += r
                all_g += g
                all_b += b

            new[y*width + x] = (
                all_r // pixel_count,
                all_g // pixel_count,
                all_b // pixel_count,
            )
            
        self._screen_pixels = new.copy()
        self._buffered = False


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

        np_canvas = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        width = self.width
        height = self.height
        for y in range(height):
            for x in range(width):
                red, green, blue = tuple(
                    clamp(x, 0, 255)
                    for x in self._screen_pixels[y*width + x]
                )
                alpha = 255
                np_canvas[y, x] = np.array([red, green, blue, alpha])

        newImage = Image.fromarray(np_canvas)
        if scale is not None:
            newImage = newImage.resize(
                (newImage.width * scale, newImage.height * scale),
                Image.Resampling.NEAREST
                )
        newImage.save(dir)

    
    # Keyboard & mouse input

    def _key_pressed_WINDOWS(self, key: str, hold: bool = True) -> bool:
        """
        Returns the pressed state of a key, designated for Windows systems.

        Refer to `key_pressed()` for the full description.
        """

        map = VK_WINDOWS

        vk = map.get(key)
        if vk is None:
            raise KeyError(f"Key {key} has not been defined in selected map.")

        current = bool(_user32.GetAsyncKeyState(vk) & 0x8000)
        previous = self._last_key_pressed.get(vk, False)

        self._last_key_pressed[vk] = current

        if hold is True:
            return current
        else:
            return current and not previous

    def _key_pressed_UNIX(self, key: str, hold: bool = True) -> bool:
        """
        Returns the pressed state of a key, designated for Unix systems.

        This is purely a fallback system. I cannot guarantee that this works.

        Refer to `key_pressed()` for the full description.
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
            previous = self._last_key_pressed.get(vk, False)

            self._last_key_pressed[vk] = current

            if hold is True:
                return current
            else:
                return current and not previous
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

    def key_pressed(self, key: str, hold: bool = True) -> bool:
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
            return self._key_pressed_WINDOWS(key=key, hold=hold)
        elif input_mode == "Unix":
            return self._key_pressed_UNIX(key=key, hold=hold)

    def _get_character(self) -> str:
        """
        [TEST METHOD] Get the output character from a key press.

        Uses the `msvcrt` module, which is exclusively for Windows.

        If a key does not have a character representation, like `DELETE` or `UP`,
        its alias will be returned.

        NOTE: This call is not asynchronous. It will block the entire program
        until a key has been detected.

        Parameters:
        - None

        Returns:
        - str
        """

        import msvcrt

        bytestr = msvcrt.getch()

        if bytestr == b'\x08': return "BACK"
        if bytestr == b'\r': return "\n"

        if bytestr != b'\xe0':
            try:
                return bytestr.decode(encoding="utf-8")
            except UnicodeDecodeError as e:
                raise Exception(repr(e))

        else:
            next_bytestr = msvcrt.getch()

            if next_bytestr == b'S': return "DELETE"

            if next_bytestr == b'H': return "UP"
            if next_bytestr == b'M': return "LEFT"
            if next_bytestr == b'P': return "DOWN"
            if next_bytestr == b'K': return "RIGHT"

            return ""

    def get_mouse_pos(self) -> tuple[int, int]:
        """
        Returns the coordinate of the mouse on the canvas.

        The coordinate can be negative, meaning the mouse is outside the terminal window.

        This method can only be used on Windows systems. There is no solution for Unix.

        Parameters:
        - None

        Returns:
        - tuple[int, int]
        """

        if input_mode != "Windows":
            raise OSError("Cannot use get_mouse_pos() on non-Windows system/terminal.")

        point = _point_t()
        if not _user32.GetCursorPos(ctypes.pointer(point)):
            return (0, 0)

        hwnd = _kernel32.GetConsoleWindow()
        if not hwnd:
            return (0, 0)

        # Get literal coordinates (device resolution)
        origin = wintypes.POINT(0, 0)
        if not _user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            return (0, 0)

        client = wintypes.RECT()
        if not _user32.GetClientRect(hwnd, ctypes.byref(client)):
            return (0, 0)

        if client.right == 0 or client.bottom == 0:
            return (0, 0)

        # Map to canvas coordinates (canvas resolution)
        mx = (point.x - origin.x) // (client.right // self.width)
        my = (point.y - origin.y) // (client.bottom // self.height)

        return (mx, my)

    
    # Window settings

    def title(self, title: str) -> None:
        """
        Set a custom title for the terminal.

        Parameters:
        - title: str

        Returns:
        - None
        """

        if input_mode == "Windows":
            _kernel32.SetConsoleTitleW(title)
        elif input_mode == "Unix":
            print(f'\33]0;{title}\a', end='', flush=True)


    # Other functions        
        
    def _in_range(
            self,
            x: int, y: int, 
            x_start: int = 0, x_end: int = None,
            y_start: int = 0, y_end: int = None
    ) -> bool:
        """
        Checks if a pixel at coordinate (x, y) is inside the visible boundary of the canvas.

        Parameters:
        - x: int
        - y: int
        - x_start: int = 0
        - x_end: int = None
        - y_start: int = 0
        - y_end: int = None

        Returns:
        - bool
        """

        if x_end is None: x_end = self.width
        if y_end is None: y_end = self.height
        return x_start <= x < x_end and y_start <= y < y_end


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
    - `canvas.width_center` and `canvas.height_center`, half of the canvas' width and height respectively
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
        
        tw, th = shutil.get_terminal_size()
        self.width = tw if width is None else width
        self.height = th if height is None else height

        self.total_pixels = self.width * self.height

        self.width_center = self.width//2
        self.height_center = self.height//2

        self._screen_pixels = []
        self._screen_buffer = []

        self._x_off = 0
        self._y_off = 0

        self.background_color = (0, 0, 0)

        #print(_SCREEN_CLEAR)
        self.clear()
        self._screen_buffer = self._screen_pixels
        self._buffered = False

        self._last_key_pressed = {}


    # Display functions

    def _plot(
            self,
            x: int, y: int, 
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
            char: str = "█",
            background_color: tuple[int, int, int, int] = None,
    ) -> None:
        """
        Plots a pixel to `_screen_pixels`, a.k.a. the canvas.

        `x`, `y`, and `color` are absolutely necessary since they define where and how to plot the pixel.
        The pixel color can be RGB or RGBA.

        `char` is the character to use.
        
        `background_color` is the background color.

        Parameters:
        - x: int
        - y: int
        - color: tuple[int, int, int, int] = (0, 0, 0, 255)
        - char: str = "█"
        - background_color: tuple[int, int, int, int] = None

        Returns:
        - None
        """

        x += self._x_off
        y += self._y_off

        width = self.width

        if background_color is None: background_color = color
        
        if self._in_range(x, y):
            if len(color) == 4 and color[3] != 255:
                color_below = self._screen_pixels[y*width + x][0:3]
                color = _combine_alpha(color, color_below)

            if len(background_color) == 4 and background_color[3] != 255:
                background_color_below = self._screen_pixels[y*width + x][4:7]
                background_color = _combine_alpha(background_color, background_color_below)
                
            self._screen_pixels[y*width + x] = (
                round_int(color[0]),
                round_int(color[1]),
                round_int(color[2]),
                char,
                round_int(background_color[0]),
                round_int(background_color[1]),
                round_int(background_color[2]),
            )

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
        height = self.height
        append = display.append
        sys_write = sys.stdout.write
        sys_flush = sys.stdout.flush

        fg = _get_foreground_color
        bg = _get_background_color

        last_p1 = None
        last_bgp1 = None

        if lock_to_terminal:
            x_range, y_range = shutil.get_terminal_size()
            x_range = min(width, x_range)
            y_range = min(height, (y_range // 2) * 2 - 1)
        else:
            x_range, y_range = width, height

        for y in range(y_range):
            row1 = y * width

            for x in range(x_range):
                i1 = row1 + x

                dp1 = self._screen_pixels[i1]
                db1 = self._screen_buffer[i1]

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
                        append(f"\033[{y+1};{x+1}H{bg(bgp1)}{fg(p1)}{cp1}")

            if y < height-1: append("\n")

        append(_COLOR_RESET)

        sys_write(''.join(display))
        sys_flush()

        self._screen_buffer = list(self._screen_pixels)
        self._buffered = True

    def clear(self) -> None:
        """
        Clears the canvas. More specifically, it fills the entire canvas with the current background color.
        """

        self._screen_pixels = [self.background_color + (' ',) + self.background_color] * self.total_pixels

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

        tw, th = shutil.get_terminal_size()
        self.width = tw if width is None else width
        self.height = th if height is None else height

        self.total_pixels = self.width * self.height

        self.width_center = self.width//2
        self.height_center = self.height//2

        self._screen_pixels = []
        self.clear()
        self._screen_buffer = self._screen_pixels

        self._buffered = False