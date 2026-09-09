# terminalCanvas

**terminalCanvas** is a Python library intended for creating graphics and developing visual-rich applications inside the terminal.

![Voxelate, a voxel-based Minecraft-wannabe game](https://raw.githubusercontent.com/RandomMaerks/terminalCanvas/main/images/readme_voxelate.png)

## Installation & Requirements

The `terminalCanvas` module currently requires Python of **version 3.10 and up**, although I've only tested on Python 3.11.

If this goes on PyPI at some point, install the module by running:

```
py -m pip install terminalCanvas
```

Otherwise, install it using Git:

```
py -m pip install git+https://github.com/RandomMaerks/terminalCanvas.git
```

The module uses `Pillow` for image processing, as well as `NumPy` for image-to-array conversion and other array-related operations. They should automatically install along with the main installation.

## How it works

Because most monospaced fonts are quite narrow (*width:height ratio is about 1:2*), we can use the half-box character `▀` to represent one squarish pixel, along with the other empty half to represent another pixel below it.

Additionally, some terminal support changing colours independently for a character (called the *foreground*) and its own background using [ANSI escape sequences](https://en.wikipedia.org/wiki/ANSI_escape_code), so we're able to fully simulate two whole pixels whose colours can be independently changed.

To create an entire canvas, we just need to fill up every space in the terminal with this character. Since one single character is able to represent two pixels, the total number of characters used should be `width * (height // 2)`, where `width` and `height` are the possible number of lines and columns respectively to write text for any given window size.

## Basic usage

The information below is only showing the very basics. For more info, please consult the wiki (doesn't exist yet lol).

### ● 2D & 3D rendering

Start by importing the main module. For convenience, set a short alias for the module, `tc` for example.

```python
import terminalCanvas as tc
```

Then, create a new `TCanvas` object:

```python
canvas = tc.TCanvas()
```

Upon creating the object, the "width" and "height" of the terminal that would run the script will automatically be detected. You can get these data by calling `canvas.width` or `canvas.height`, as well as the precalculated `canvas.wCenter` and `canvas.hCenter`.

Some properties of the canvas can be changed. For example, to change the background colour:

```python
canvas.background((125, 170, 245))
```

The `background()` method requires a *tuple* with three items that represents the RGB values.

To resize the canvas, use:

```python
canvas.resize()
```

This will replace the old `canvas.width` and `canvas.height` with the new values corresponding to the reoslution of the terminal window. This is especially important if you want to resize the terminal window during runtime.

To create a graphical object such as a line, you can call the `Line` class:

```python
line = tc.Line(0, 0, canvas.width, canvas.height, color=(255, 0, 0))
```

This will create an instance of the `Line` class which includes the line's pixel data, its attributes, and additional setter methods to modify them. Other objects include `Point`, `Point3D`, `Line3D`, `Rectangle`, `Triangle`, `Triangle3D`, `Ellipse`, `Text`, `Image`, and `Sprite`. Their attributes do not need to be set right from the start; you can simply create an instance of any object with absolutely no arguments.

Anyway, we've created an object, but it's not on the canvas yet. To actually draw the line, use the `draw()` method:

```python
canvas.draw(line)
```

This will put all the pixels from the object into the main canvas.

Now, to show the canvas and see what you've drawn, use:

```python
canvas.show()
```

This will print everything in our canvas to the terminal.

![An example of the line being drawn on the canvas](https://raw.githubusercontent.com/RandomMaerks/terminalCanvas/main/images/readme_lineExample.png)

However, `canvas.show()` only shows the canvas once. You can put it in a loop to keep it running, along with `keyPressed()` to stop the loop using keyboard input:

```python
while True:
    if canvas.keyPressed("ESC"):
        break

    canvas.clear()

    # all the drawing stuff

    canvas.show()
```

The `clear()` method allows the canvas to be completely clean before redrawing anything for the next frame. Without calling this method, the very first frame will be the only frame to be shown.

Lastly, you should put `canvas.end()` after everything to properly erase everything and restore the cursor.

The whole thing should be something like this:

```python
import terminalCanvas as tc

canvas = tc.TCanvas()
canvas.background((125, 170, 245))

line = tc.Line(
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

### ● User interface

**terminalCanvas** also has a canvas dedicated to "user interface", although it is very limited. You can use it by calling `TCanvasUI` instead of `TCanvas`:

```python
canvas = tc.TCanvasUI()
```

`TCanvasUI` fundamentally changes what a "pixel" is on the canvas and how each pixel is represented. In `TCanvas`, each pixel represents one color, takes up half of a character's bounding box, and the glyph used in this character space is specifically the half-box character `▀`. In `TCanvasUI`, however, each pixel represents one character, and the glyph is either a letter from a textbox or part of a rectangular frame.

By default, the background color of `TCanvasUI` will be entirely black, as opposed to `TCanvas` being white. You can still change it using `background()`.

There are two custom graphical objects for `TCanvasUI`: `RectangleUI` and `TextUI`.

You can use it like the other objects:

```python
tc.RectangleUI(
    0, 0,
    canvas.width - 1, canvas.height - 1,
    color=(255, 0, 0),
    mode="frame",
)
```

While non-UI objects are usable in `TCanvasUI`, they will not be displayed in the same manner as in `TCanvas`.

`TCanvasUI` also has all the essential methods like `draw()` and `show()`.

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