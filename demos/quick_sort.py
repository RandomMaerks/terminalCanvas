import random
import time
from colorsys import hsv_to_rgb

import terminalCanvas as tc
from terminalCanvas import map

def get_matches(list1, list2) -> list:
    return [x for x in range(len(list1)) if list1[x] == list2[x]]

def show_numbers(
    color = (255, 255, 255),
    highlight: list = None,
    delay: float = 0,
    clear: bool = True,
    use_cache: bool = True,
):
    global cached_arr

    if clear: canvas.clear()

    line = tc.Line()

    for i, value in enumerate(arr):
        hue = map(value, 1, elements, 0, 1)
        new_color = hsv_to_rgb(hue, 1.0, 1.0)
        line.set_color(
            color
            if (highlight and i in highlight)
            else tuple(_ * 255 for _ in new_color)
        )

        height = map(value, 0, elements, 0, canvas.height)

        line.set_points(
            i, canvas.height - height,
            i, canvas.height - 1,
        )
        canvas.draw(line)

        if delay != 0 and not (use_cache and arr[i] == cached_arr[i]):
            canvas.show()
            time.sleep(delay)

    canvas.show()

    cached_arr = arr.copy()

canvas = tc.TCanvas()
canvas.background((0, 0, 0))
canvas.title("Quick sort demo")

elements = canvas.width

arr = [x+1 for x in range(elements)]
sorted_arr = sorted(arr)
cached_arr = arr.copy()

# -----------------
# MAIN DRAW PROCESS
# -----------------

# First display
show_numbers()
time.sleep(0.5)

# Shuffle the list
iterations = elements * 2
for _ in range(iterations):
    index1 = random.randrange(0, elements)
    index2 = random.randrange(0, elements)

    arr[index1], arr[index2] = arr[index2], arr[index1]
    show_numbers(
        color = (255, 255, 255),
        highlight = [index1, index2]
    )
show_numbers()
time.sleep(0.5)

# Put list through the sorting algorithm
def quick_sort(start: int, end: int):
    """
    This implementation of Quicksort prioritises
    the "good-lookingness" of the visualisation
    rather than speed or efficiency.
    """
    
    global arr

    if start >= end - 1: return

    small_arr = arr[start:end]
    pivot = small_arr[-1]

    left = [x for x in small_arr if x < pivot]
    right = [x for x in small_arr if x > pivot]

    new_arr = left + [pivot] + right

    for i in range(start, end):
        arr[i] = new_arr[i - start]
        show_numbers(
            highlight = [i]
        )

    quick_sort(start, start + len(left))
    quick_sort(end - len(right), end)

    show_numbers()

quick_sort(0, elements)

# Color all correctly sorted elements GREEN for an amazing reason
show_numbers(
    color = (0, 255, 0),
    highlight = get_matches(arr, sorted_arr),
    delay = 0.01,
    clear = False,
    use_cache = False,
)

time.sleep(1)

canvas.end()