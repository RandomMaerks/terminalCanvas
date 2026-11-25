from math import pi
import random
import time
from colorsys import hsv_to_rgb

try:
    from perlin_noise import PerlinNoise
except ModuleNotFoundError as e:
    print(
        "The module \"perlin_noise\" is not part of "
        "terminalCanvas. Install it manually using "
        "`py -m pip install perlin_noise`."
    )
    raise ModuleNotFoundError

import terminalCanvas as tc
from terminalCanvas import map

canvas = tc.TCanvas()
canvas.background((0, 0, 0))
canvas.depth_intensity = 0.002

camera = tc.Camera()
camera.rotate(ax=-pi/16)
camera.move(y=30, z=-15)

scale = 20
w, h = 400, 400
cols = w // scale
rows = h // scale

noise = PerlinNoise(octaves=4, seed=50)

line = tc.Line3D(color=(255, 255, 255))

frame_index = 0
current_y = 0
while True:
    if canvas.key_pressed("ESC"):
        break

    canvas.clear()

    terrain = [
        [0 for _ in range(rows)]
        for _ in range(cols)
    ]
        
    y_off = current_y
    for y in range(rows):
        x_off = 0
        for x in range(cols):
            terrain[x][y] = tc.map(noise([x_off, y_off]), 0, 1, -10, 40)
            x_off += 0.1
        y_off += 0.1

    for y in range(rows - 1):
        for x in range(cols - 1):
            p1 = x*scale - w/2, terrain[x][y], y*scale
            p2 = x*scale - w/2, terrain[x][y+1], (y+1)*scale

            p3 = (x+1)*scale - w/2, terrain[x+1][y], y*scale
            p4 = (x+1)*scale - w/2, terrain[x+1][y+1], (y+1)*scale

            new_color = hsv_to_rgb(
                map(p1[2] + frame_index, 0, w, 0, 1),
                1,
                map(p1[2], 0, h, 1.25, -0.5),
            )
            line.set_color(tuple(_ * 255 for _ in new_color))

            line.set_points(*p1, *p2)
            canvas.draw(line, camera)

            line.set_points(*p2, *p3)
            canvas.draw(line, camera)
            
            line.set_points(*p2, *p4)
            canvas.draw(line, camera)

            if x == cols - 2:
                line.set_points(*p3, *p4)
                canvas.draw(line, camera)
    
    canvas.invert()
    canvas.show()

    current_y += 0.01
    frame_index += 1

canvas.end()