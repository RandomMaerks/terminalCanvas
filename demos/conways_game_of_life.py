import time
from colorsys import hsv_to_rgb
import random

import terminalCanvas as tc

class Clock:
    def __init__(self, fps: int = 60) -> None:
        self.set_fps(fps)

    def set_fps(self, fps: int) -> None:
        self._fps = fps
        self._frame_time = 1 / fps
        self._next_frame = 0

    def tick(self) -> bool:
        self._next_frame += self._frame_time
        sleep_time = self._next_frame - time.perf_counter()

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            self._next_frame = time.perf_counter()

        return True

clock = Clock(20)

canvas = tc.TCanvas()
width, height = canvas.width, canvas.height
canvas.background((0, 0, 0))

grid = [
    [random.randint(0, 1) for _ in range(width)]
    for _ in range(height)
]

life_duration = [
    [0 for _ in range(width)]
    for _ in range(height)
]

live_cell = tc.Point(color=(0, 0, 0))

running = False
canvas.title("running = False")

while clock.tick():
    if canvas.key_pressed("ESC"):
        break

    if canvas.key_pressed("S", hold=False):
        running = not running
        canvas.title(f"running = {running}")
    
    if canvas.key_pressed("Z"):
        mx, my = canvas.get_mouse_pos()
        if canvas._in_range(mx, my):
            grid[my][mx] = 1

    if canvas.key_pressed("X"):
        mx, my = canvas.get_mouse_pos()
        if canvas._in_range(mx, my):
            grid[my][mx] = 0

    if running:
        new_grid = [
            [0 for _ in range(width)]
            for _ in range(height)
        ]

        for y in range(height):
            for x in range(width):
                indices = (
                    (y - 1, x - 1),
                    (y - 1, x),
                    (y - 1, x + 1),
                    (y, x - 1),
                    (y, x + 1),
                    (y + 1, x - 1),
                    (y + 1, x),
                    (y + 1, x + 1),
                )
                neighbour_count = sum(grid[a % height][b % width] for a, b in indices)

                if (grid[y][x] == 1 and 2 <= neighbour_count <= 3) \
                    or (grid[y][x] == 0 and neighbour_count == 3):
                    new_grid[y][x] = 1
                    life_duration[y][x] += 1
                else:
                    life_duration[y][x] = 0

        grid = new_grid.copy()

    canvas.clear()
    for y in range(height):
        for x in range(width):
            if grid[y][x] == 1:
                live_cell.set_points(x, y)

                life = life_duration[y][x]
                new_color = hsv_to_rgb((4 * life) / 360, 1, 1 - 1 / (0.05 * life + 1))
                live_cell.set_color(tuple(_ * 255 for _ in new_color))

                canvas.draw(live_cell)

    canvas.show()

canvas.end()