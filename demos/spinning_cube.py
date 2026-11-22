from math import cos, sin, pi, degrees, atan2, sqrt
from colorsys import hsv_to_rgb
import time

import terminalCanvas as tc
from terminalCanvas import map

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

clock = Clock(60)

canvas = tc.TCanvas()
canvas.background((0, 0, 0))
canvas.depth_intensity = 0.07
canvas.depth_accuracy = 2
canvas.title("Spinning cube demo. Press ESC to exit.")

mult = 0.01

theta = 0
d_theta = 2 * mult
phi = 0
d_phi = 3 * mult
r = 3

camera = tc.Camera(x=0, z=r, ax=-pi)
camera.fov(100)

cube = tc.Cube(length=1, color=(255, 0, 0), mode="solid")
frame = tc.Cube(length=1, color=(255, 255, 255), mode="frame")

while clock.tick():
    if canvas.key_pressed("ESC"):
        break

    theta += d_theta
    phi += d_phi

    new_length = abs(cos(theta))
    cube.set_length(new_length)

    hue = map(theta % pi, 0, pi, 0, 1)
    new_color = tuple(_ * 255 for _ in hsv_to_rgb(hue, 1, 1))
    cube.set_color(new_color)

    st = sin(theta)
    ct = cos(theta)
    sp = sin(phi)
    cp = cos(phi)

    x = r * st * cp
    y = r * st * sp
    z = r * ct

    camera.set_position(x, y, z)
    camera.set_angle(
        ax = -atan2(y, sqrt(x*x + z*z)),
        ay = atan2(-x, z) - pi,
    )

    canvas.clear()

    canvas.draw(cube, camera)
    canvas.draw(frame, camera)

    blur_radius = abs(int((st-sin(pi/2))**2 + 5*sp**7))
    canvas.blur(radius=blur_radius)

    canvas.show()

canvas.end()