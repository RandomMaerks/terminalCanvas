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
            font = font_5x7

        kerning_info = font.get("kerning", dict())
        
        x_curr = x1
        y_curr = y1
        
        for message in messages:
            text_lines = []
            total_width = 0
            glyph = []

            for index, char in enumerate(message):
                if char not in font:
                    x_curr += 4 + spacing
                    total_width += 4 + spacing
                    continue

                glyph_data = font.get(char)

                glyph = glyph_data.get("bitmap")
                next_x = glyph_data.get("next_x", 0)
                offset_x = glyph_data.get("offset_x", 0)
                offset_y = glyph_data.get("offset_y", 0)
                
                charWidth = len(glyph[0])

                kern = kerning_info.get(f"{message[index-1]}{char}", 0) if index > 0 else 0

                for y, row in enumerate(glyph):
                    line = []
                    for x, data in enumerate(row):
                        line.append([
                            data, 
                            x_curr + x + kern + offset_x, 
                            y_curr + y + offset_y,
                            color
                        ])
                    text_lines.append(line)

                total_offset = charWidth + spacing + kern + next_x + offset_x
                
                x_curr += total_offset
                total_width += total_offset
            
            x_curr = x1
            y_curr += len(glyph)

            if anchor_x == "left": xOff = 0
            elif anchor_x == "center": xOff = -(total_width)//2
            elif anchor_x == "right": xOff = -(total_width)

            if anchor_y == "top": yOff = 0
            elif anchor_y == "center": yOff = -len(text_lines[0])//2
            elif anchor_y == "bottom": yOff = -len(text_lines[0])

            for line in text_lines:
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