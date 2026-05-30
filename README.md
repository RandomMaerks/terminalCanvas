# terminalCanvas

**terminalCanvas** is a Python library intended for creating graphics and developing visual-rich applications inside the terminal.

![Voxelate, a voxel-based Minecraft-wannabe game](https://raw.githubusercontent.com/RandomMaerks/terminalCanvas/main/images/readme_voxelate.png)

## How it works

Because most monospaced fonts are quite narrow (*width:height ratio is about 1:2*), we can use the half-box character `▀` to represent one squarish pixel, along with the other empty half to represent another pixel below it.

Additionally, some terminal support changing colours independently for a character (called the *foreground*) and its own background using [ANSI escape sequences](https://en.wikipedia.org/wiki/ANSI_escape_code), so we're able to fully simulate two whole pixels whose colours can be independently changed.

To create an entire canvas, we just need to fill up every space in the terminal with this character. Since one single character is able to represent two pixels, the total number of characters used should be `width * (height // 2)`, where `width` and `height` are the possible number of lines and columns respectively to write text for any given window size.

## Installation & Requirements

The `terminalCanvas` module currently requires Python of **version 3.10 and up**, although I've only tested on Python 3.11.

If this goes on PyPI at some point, install the module by running:

```
py -m pip install terminalCanvas
```

Otherwise, just do:

```
py -m pip install git+https://github.com/RandomMaerks/terminalCanvas.git
```

The module uses `Pillow` for image processing, as well as `NumPy` for image-to-array conversion and other array-related operations. They should automatically install along with the main installation.

## Basic usage

The information below is only showing the very basics. For more info, please consult the wiki (doesn't exist yet lol).

### ● 2D rendering

Start by importing the main module:

```python
import terminalCanvas
```

Then, create a new `TCanvas` object:

```python
canvas = terminalCanvas.TCanvas()
```

Upon creating the object, the "width" and "height" of the terminal that would run the script will automatically be detected by the `shutil` module and cannot (or should not) be changed. You can get these data by calling `canvas.width` or `canvas.height`, as well as the precalculated `canvas.wCenter` and `canvas.hCenter`.

Some properties of the canvas can be changed. For example, to change the background colour:

```python
canvas.background((125, 170, 245))
```

The `TCanvas.background()` method requires a *tuple* with three items that represents the RGB values.

To create a graphical object such as a line, you can call the `TCanvas.line()` method:

```python
line = canvas.line(0, 0, canvas.width, canvas.height, color=(255, 0, 0))
```

This method will initialise and return a new `TC_Line` object. The initialisation calculates all the pixels that make up the line and saves it in a list. Other objects include `TC_Point`, `TC_Rectangle`, `TC_Triangle`, `TC_Ellipse`, `TC_Text`, `TC_Image`, and `TC_Sprite`, initialised by calling the respective method with the same name, just without the `TC_` prefix and in lowercase.

However, it's not on the canvas. To actually draw the line, use the `TCanvas.draw()` method:

```python
canvas.draw(line)
```

This will put all the pixels from the object into the main canvas, saved in the attribute `TCanvas.screenPixels`. Note that all the methods here are from the `TCanvas` class, not the actual objects.

Now, to show the canvas and see what you've drawn, use:

```python
canvas.show()
```

This will print everything in `TCanvas.screenPixels` to the terminal.

![An example of the line being drawn on the canvas](https://raw.githubusercontent.com/RandomMaerks/terminalCanvas/main/images/readme_lineExample.png)

Lastly, you should put `canvas.end()` after everything to properly erase everything and restore the cursor.

However, `TCanvas.show()` only shows the canvas once. You can put it in a loop to keep it running, along with another method call `TCanvas.keyPressed()` to exit it using keyboard input:

```python
while True:
    if canvas.keyPressed("ESC"):
        break

    canvas.clear()

    # all the drawing stuff

    canvas.show()
```

The `TCanvas.clear()` method allows the canvas to be completely clean before redrawing anything for the next frame. Without calling this method, the very first frame will be the only frame to be shown.

The whole thing should be something like this:

```python
import terminalCanvas

canvas = terminalCanvas.TCanvas()
canvas.background((125, 170, 245))

line = canvas.line(
    0, 0,
    canvas.width, canvas.height,
    color=(255, 0, 0)
)

while True:
    if canvas.keyPressed("ESC"):
        break

    canvas.clear()
    canvas.draw(line)
    canvas.show()

canvas.end()
```

### ● 3D rendering

**terminalCanvas** also supports 3D rendering, although it is very limited. You can use it by calling `TCanvas3D` instead of `TCanvas`:

```python
canvas = terminalCanvas.TCanvas3D()
```

Everything in `TCanvas` is inherited, and some other methods are added specifically for 3D rendering.

One custom graphical object for `TCanvas3D` is `TC_Triangle3D`, initialised by the method `TCanvas3D.triangle3D()`. This object takes three points in three dimensions, with the `z` value being used as the layer or precedence of a pixel. Basically, a pixel with a low `z` index is drawn on top of another with a higher `z` index, or lower `z` indices are closer to the "viewport".

You can use it like the other objects:

```python
canvas.triangle3D(
    x1, y1, z1,
    x2, y2, z2,
    x3, y3, z3,
    color=color
)
```

You can still use 2D objects with the 3D ones, but the 2D ones will always be on top.

`TCanvas3D` also has all the essential methods like `draw()` and `show()`.

## Credits & honourable mentions

Massive thanks to [**ConnerWill**](https://connerwill.com/) for his [ANSI escape sequence cheatsheet](https://gist.github.com/ConnerWill/d4b6c776b509add763e17f9f113fd25b). Without this cheatsheet, I wouldn't have been able to make this module possible (and, honestly, I wouldn't have known that this entire thing was possible).

Another huge thanks to [**Gabriel Gambetta**](https://www.gabrielgambetta.com/index.html) for writing the book [Computer Graphics from Scratch](https://www.gabrielgambetta.com/computer-graphics-from-scratch/). All my rasterisation work closely follow his guidance.

I'd also like to mention Mr. Shiffman, [**Daniel Shiffman**](https://github.com/shiffman) from [The Coding Train](https://www.youtube.com/thecodingtrain) for inspring me to do programming with all his fascinating coding challenges.

Some honourable mentions:

- [`p5.js`](https://p5js.org/), literally where this whole idea comes from
- The [`pyglet`](https://pyglet.readthedocs.io/en/latest/) module

Other credits:

- [Virtual key codes](https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes)
- [Bresenham's line algorithm](https://en.wikipedia.org/wiki/Bresenham's_line_algorithm)