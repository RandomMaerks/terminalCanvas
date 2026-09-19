class BaseObject:
    """
    The base object class for all terminalCanvas's objects.
    Mainly for people who want to make shapes and other graphics that can be used in `TCanvas`.

    To make a child object of `BaseObject`, write: `class <ObjectName>(BaseObject):`.

    There are public and private methods that should not be overridden, except for `_build()`.

    `_build()` is a required method which calculates all the pixels that make up the intended object.
    You must have a `_build()` method for your object and it must have `self._empty()` at the very start.
    While building, you can use `self._add(x, y, color)` to add a pixel to the pixel data. Color can be RGB or RGBA.

    There is also the `_modified` attribute, denoting the necessity to be rebuilt when drawn to the canvas.
    When it is drawn, this attribute changes to `False` and will stay as `False` until an attribute is changed where it is set to `True`.
    Every attribute setter method needs to set `_modified` to `True` at the end, otherwise the changes will not apply.

    You can add more methods like getter or setter methods.

    Public methods:
    - `move(x, y)`: move the object by some x and y pixels
    - `scale(x)`: scale the object up by a factor of integer x
    - `set_color((R, G, B[, A]))`: change the color of the object
    - `collides(other)`: detect collision of self with other
    - `includes((x, y))`: detect coordinate on pixel data of self

    Private methods:
    - `_empty()`: reset pixel data and edges
    - `_add(x, y, (R, G, B[, A]))`: add pixel to pixel data, as well as updating edges
    - `_build()`: recalculate pixel data
    
    Attributes:
    - `data`: a list of pixels, each of which contains coordinate and color data
    - `left`, `right`, `top`, `bottom`: edges of the object
    - `_modified`: state of object, whether its attributes have been modified
    """

    def __init__(self) -> None:
        """
        Initialises `BaseObject`.
        """
        self._modified = False
        self._empty()

    def _empty(self):
        """
        Refreshes pixel data and edges for building.
        """

        self.data = []
        self.left = self.right = self.top = self.bottom = 0

    # Pixel insertion, edge detection

    def _add(self, pixel: list) -> None:
        self.data.append(pixel)

        x, y, *_ = pixel
        if x < self.left: self.left = x
        if x > self.right: self.right = x
        if y < self.top: self.top = y
        if y > self.bottom: self.bottom = y

    # Empty build method

    def _build(self):
        raise NotImplementedError

    # Object transformation

    def move(self, xShift: int, yShift: int) -> None:
        self.data = [
            [x + xShift, y + yShift, color, *_]
            for x, y, color, *_ in self.data
        ]

    def scale(self, amount: int) -> None:
        xAnchor = (self.right - self.left) // 2
        yAnchor = (self.bottom - self.top) // 2
        scaled = []
        for x, y, color, *_ in self.data:
            xShift = (x - xAnchor) * (amount - 1)
            yShift = (y - yAnchor) * (amount - 1)
            for i in range(amount):
                for j in range(amount):
                    scaled.append([x + i + xShift, y + j + yShift, color, *_])
        self.data = scaled

    def set_color(self, color: tuple[int, int, int, int]) -> None:
        self.color = color
        self._modified = True

    # Collision detection

    def collides(self, other) -> bool:
        pixels1 = set((x, y) for x, y, *_ in self.data)
        pixels2 = set((x, y) for x, y, *_ in other.data)

        return not pixels1.isdisjoint(pixels2)

    # Other methods

    def __contains__(self, point: tuple[int, int]) -> bool:
        pixels = set((x, y) for x, y, *_ in self.data)

        return point in pixels