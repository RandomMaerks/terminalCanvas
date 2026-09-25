class BaseCompoundObject:
    """
    The base compound object class consisting of multiple BaseObject shapes.

    To make a subclass of `BaseCompoundObject`, write: `class <ObjectName>(BaseCompoundObject):`.
    Then, use `super().__init__()` to call the BaseCompoundObject `__init__` method.
    This will ensure all the required attributes are present in the child class.

    `_build()` is a required method which calculates all the necessary shapes that make up the intended compound object.
    You must have a `_build()` method for your object and it must have `self._empty()` at the very start.

    All BaseObject shapes that make up the BaseCompoundObject shape should go in `self.objects`, simply by doing `self._add(object)`.
    Their attributes depend on what you want to achieve with your compound object.
    e.g. `self._add(Line3D(-1, 0, 0, 1, 0, 0, color=(255, 0, 0)))` adds an instance of Line3D to the object data.
    
    For setter methods, make sure to apply the changes to **every single object in `self.objects`**.
    This is merely a reminder, but it's still important to check.
    Additionally, set `_modified` to True for each object (e.g. `for obj in self.objects: obj._modified = True`).

    Public methods:
    - `move(x, y)`: move all objects by some x and y pixels
    - `scale(x)`: scale all objects up by a factor of integer x
    - `set_color((R, G, B[, A]))`: change the color of all objects (change if colors are different between objects)
    - `collides(other)`: detect collision of self with other (other being BaseObject and its subclasses)
    - `includes((x, y))`: detect coordinate on pixel data of self

    Private methods:
    - `_empty()`: reset object data
    - `_add(object: BaseObject)`: add object to object data
    - `_build()`: recalculate object data
    
    Attributes:
    - `data`: a list of pixels, each of which contains coordinate and color data
    - `_modified`: state of object, whether its attributes have been modified
    - `_compound`: indicator for TCanvas. Do not delete or modify.
    """

    def __init__(self) -> None:
        """
        Initialises `BaseCompoundObject`.
        """
        self._modified = True
        self._compound = True
        self._empty()

    def _empty(self):
        """
        Refreshes object data.
        """

        self.objects = []

    # Object insertion

    def _add(self, object: "BaseObject") -> None:
        self.objects.append(object)

    # Empty build method

    def _build(self) -> None:
        raise NotImplementedError

    # Object transformation

    def move(self, xShift: int, yShift: int) -> None:
        for obj in self.objects:
            obj.move(xShift, yShift)

    def scale(self, amount: int) -> None:
        for obj in self.objects:
            obj.scale(amount)

    def set_color(self, color: tuple[int, int, int, int]) -> None:
        for obj in self.objects:
            obj.color = color
            obj._modified = True

    # Collision detection

    def collides(self, other) -> bool:
        for obj in self.objects:
            pixels1 = set((x, y) for x, y, *_ in obj.data)
            pixels2 = set((x, y) for x, y, *_ in other.data)

            if not pixels1.isdisjoint(pixels2): return True

        return False

    # Other methods

    def __contains__(self, point: tuple[int, int]) -> bool:
        for obj in self.objects:
            pixels = set((x, y) for x, y, *_ in self.data)

            if point in pixels: return True

        return False