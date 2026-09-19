def clamp(v, lo, hi):
    """
    Bound a value to a specific range.

    The first parameter, `v`, is the target value to bound.
    The next two parameters are `lo` and `hi` which represent the lower and upper limits respectively.

    If `lo` <= `v` <= `hi`, `v` will be returned. If `v` < `lo`, `lo` is returned. If `v` > `hi`, `hi` is returned.

    For example, `clamp(1, 100, 999)` returns `100`, `clamp(145, 0, 255)` returns `145`, and `clamp(1.0, 0.0, 1.0)` returns `1.0`.

    This implementation uses the `<` and `>` operators, meaning any data type that supports
    these operators should work.

    Parameters:
    - v
    - lo
    - hi
    """

    return lo if v < lo else hi if v > hi else v

def map(v, old_lo, old_hi, new_lo, new_hi):
    """
    Map a value from an "old" range to a "new" one.

    The first parameter, `v`, is the target value to map.
    The next two parameters are `old_lo` and `old_hi` which represent the lower and upper limits of the old range.
    The last two, `new_lo` and `new_hi`, represent the limits of the new range.

    For example, `map(0.05, 0, 1, 0, 255)` returns 12.75.

    This value is calculated using the formula:
    `(v - old_lo) / (old_hi - old_lo) * (new_hi - new_lo) + new_lo`.
    If the lower and upper limits of the old range is 0, the lower limit of the new range is returned instead.

    Parameters:
    - v
    - old_lo
    - old_hi
    - new_lo
    - new_hi
    """

    if old_lo != old_hi:
        return (v - old_lo) / (old_hi - old_lo) * (new_hi - new_lo) + new_lo
    else:
        return new_lo

def roundInt(x: float) -> int:
    """
    Rounds a float to the nearest whole integer.

    For example, `roundInt(0.1)` returns 0, while `roundInt(0.7)` returns 1.
    `roundInt(0.5)` returns 1.

    Parameters:
    - x: float

    Returns:
    - int
    """

    try:
        return int(x + 0.5) if x >= 0 else int(x - 0.5)
    except TypeError as e:
        raise TypeError(repr(e) + f" (offender: {x})")

def interpolate(i0, d0, i1, d1, round = True) -> list:
    if i0 == i1:
        return [roundInt(d0) if round else d0]

    n = i1 - i0
    values = [0] * (n + 1)

    r = roundInt if round else lambda x: x

    delta = (d1 - d0) / n
    d = d0

    for i in range(n + 1):
        values[i] = r(d)
        d += delta

    return values

def range_float(start: float, stop: float, step: float):
    curr = start
    while curr <= stop:
        yield curr
        curr += step