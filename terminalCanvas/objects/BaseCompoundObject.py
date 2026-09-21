class BaseCompoundObject:
    """
    The base compound object class consisting of multiple BaseObject shapes.

    To make a subclass of `BaseCompoundObject`, write: `class <ObjectName>(BaseCompoundObject):`.
    Then, use `super().__init__()` to call the BaseCompoundObject `__init__` method.
    This will ensure all the required attributes are present in the child class.

    All BaseObject shapes that make up the BaseCompoundObject shape should go in `self.objects`, simply by doing `self.objects.append()`.
    Then, when drawn, the canvas will look through this list and automatically pick up all of those shapes.

    You can simply make all the calculations for the desired shapes in `__init__(self)`,
    or add your own methods for more nuanced computations.

    For setter methods, make sure to apply the changes to **every single object in `self.objects`**.
    This is merely a reminder, but it's still important to check.
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

    def _add(self, object: BaseObject) -> None:
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