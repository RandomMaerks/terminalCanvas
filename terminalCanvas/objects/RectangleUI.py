from .BaseObject import BaseObject
from ..Coord import Coord

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