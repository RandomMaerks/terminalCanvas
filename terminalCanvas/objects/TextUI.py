import textwrap

from .BaseObject import BaseObject
from ..Coord import Coord

class TextUI(BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            message: str = "",
            anchor_x: str = "left",
            max_width: int = None,
            max_height: int = None,
            cutoff: str = "whole",
            color: tuple[int, int, int, int] = (255, 255, 255, 255),
            bgcolor: tuple[int, int, int, int] = (0, 0, 0, 0),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.message = message
        self.anchor_x = anchor_x
        self.color = color
        self.bgcolor = bgcolor
        self.max_width = max_width
        self.max_height = max_height
        self.cutoff = cutoff
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)

        messages = self.message.split("\n")
        anchor_x = self.anchor_x
        color = self.color
        bgcolor = self.bgcolor
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
                    newtext = textwrap.wrap(
                        message,
                        width = max(1, max_width)
                    )
                    for text in newtext:
                        sepmessages.append(text)
                            
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
                self._add([x1 + x + xOff, y1 + y, color, char, bgcolor])

            y += 1

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True

    def set_bgcolor(self, bgcolor: tuple[int, int, int, int]):
        self.bgcolor = bgcolor
        self._modified = True

    def set_message(self, message):
        self.message = message
        self._modified = True

    def set_anchor_x(self, anchor_x):
        self.anchor_x = anchor_x
        self._modified = True

    def set_max_width(self, max_width):
        self.max_width = max_width
        self._modified = True

    def set_max_height(self, max_height):
        self.max_height = max_height
        self._modified = True

    def set_cutoff(self, cutoff):
        self.cutoff = cutoff
        self._modified = True

    def __copy__(self):
        return TextUI(
            *self.p1,
            message = self.message,
            anchor_x = self.anchor_x, anchor_y = self.anchor_y,
            max_width = self.max_width, max_height = self.max_height,
            cutoff = self.cutoff,
            color = self.color,
            bgcolor = self.bgcolor
        )