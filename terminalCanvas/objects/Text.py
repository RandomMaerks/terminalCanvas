from .BaseObject import BaseObject
from ..Coord import Coord
from ..fonts import font_5x7

class Text(BaseObject):
    def __init__(
            self, 
            x1: int | float = 0, y1: int | float = 0, 
            message: str = "",
            font: dict = None, 
            spacing: int = 0,
            anchor_x: str = "left",
            anchor_y: str = "top",
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
    ) -> None:

        super().__init__()

        self.p1 = Coord(x1, y1)
        self.message = message
        self.font = font
        self.spacing = spacing
        self.anchor_x, self.anchor_y = anchor_x, anchor_y
        self.color = color
        self._build()

    def _build(self):
        self._empty()
        
        x1, y1 = round(self.p1)

        messages = self.message.split("\n")
        font = self.font
        spacing = self.spacing
        anchor_x, anchor_y = self.anchor_x, self.anchor_y
        color = self.color   

        if font is None:
            font = font_5x7.regular  

        kerningInfo = font.get("kerning", dict())
        next_xInfo = font.get("next_x", dict())
        offset_xInfo = font.get("offset_x", dict())
        offset_yInfo = font.get("offset_y", dict())
        
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
                offset_x = offset_xInfo.get(char, 0)
                offset_y = offset_yInfo.get(char, 0)

                kern = kerningInfo.get(f"{message[index-1]}{char}", 0) if index > 0 else 0

                for y, row in enumerate(glyph):
                    line = []
                    for x, data in enumerate(row):
                        line.append([
                            data, 
                            xCurrent + x + kern + offset_x, 
                            yCurrent + y + offset_y,
                            color
                        ])
                    textLines.append(line)

                xCurrent += charWidth + spacing + kern + next_x + offset_x
                totalWidth += charWidth + spacing + kern + next_x + offset_x
            
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
                    if data == "1": self._add([x + xOff, y + yOff, color])

    def set_points(self, x1, y1):
        self.p1 = Coord(x1, y1)
        self._modified = True

    def set_message(self, message):
        self.message = message
        self._modified = True

    def set_font(self, font):
        self.font = font
        self._modified = True

    def set_spacing(self, spacing):
        self.spacing = spacing
        self._modified = True

    def set_anchor_x(self, anchor_x):
        self.anchor_x = anchor_x
        self._modified = True

    def set_anchor_y(self, anchor_y):
        self.anchor_y = anchor_y
        self._modified = True

    def __copy__(self):
        return Text(
            *self.p1,
            message = self.message,
            font = self.font,
            spacing = self.spacing,
            anchor_x = self.anchor_x, anchor_y = self.anchor_y,
            color = self.color
        )