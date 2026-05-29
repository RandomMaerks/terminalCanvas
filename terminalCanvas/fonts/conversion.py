class UnsupportedFileTypeError(Exception):
    pass

class InvalidBDFStructure(Exception):
    pass

# ---------------------------------
# BDF to TC_Text-usable dict format
# ---------------------------------

'''
More details on the Bitmap Distribution Format (BDF) can be found on
https://adobe-type-tools.github.io/font-tech-notes/pdfs/5005.BDF_Spec.pdf

Global font information:
- STARTFONT number          -> number defines version of file format
- COMMENT string            -> comments to ignore
- CONTENTVERSION integer    -> (opt.) version of content/data
- FONT string               -> PostScript(TM) language font name
- SIZE PointSize Xres Yres  -> point size & intended x, y res of device
- FONTBOUNDINGBOX FBBx FBBy Xoff Yoff   -> max width & max height, and x y displacement of lower left corner from 0
- METRICSSET integer        -> (opt.) 0(def)=writing direction 0 (hor), 1=1 (ver), 2=both. Check the spec for better understanding.
- STARTPROPERTIES n         -> (opt.) n properties to read in the next n lines (prop. format: PROPNAME "value")
- ENDPROPERTIES             -> denote end of reading properties

Individual glyph information:
- CHARS nglyphs             -> nglyphs number of glyphs defined in the font
- STARTCHAR string          -> denote start of reading char, string is name of glyph (PostScript)
- ENCODING integer          -> +int representing Adobe Standard Encoding Value, -1 + glyphIndex if not
- SWIDTH swx0 swy0          -> scalable width in x, y for writing mode 0, unit 1/1000th size of glyph
- DWIDTH dwx0 dwy0          -> width in x, y in device pixels. Is mandatory for writing mode 0
- SWIDTH1 swx1 swy1         -> scalable width in x, y for writing mode 1.
- DWIDTH1 dwx1 dwy1         -> width in x, y in integer pixels. Is mandatory for writing mode 1
    + METRICSSET = 1 or 2   -> SWIDTH1 and DWIDTH1 are mandatory
    + METRICSSET = 0        -> both should be absent
- VVECTOR xoff yoff         -> components of a vector from 0 to 1. Check the spec for better understanding.
- BBX BBw BBh BBxoff0x BByoff0y         -> width BBw of black pixels in x, height BBh in y, and x y displacement.
- BITMAP (newline) <hexData>-> denote start of bitmap. hexData to represent pixel presence per line in hex (to bin: 1=pixel, 0=empty)
- ENDCHAR                   -> denote end of reading char
- ENDFONT                   -> denote end of reading font. error cond. if called before all glyphs have been read
'''

def from_bdf(font_dir: str) -> list:
    if not font_dir.endswith(".bdf"):
        raise UnsupportedFileTypeError(f"Must be of type '.bdf' for this conversion.")

    with open(font_dir, "r") as font:
        data = font.readlines()

    font = {
        "kerning" : {},
        "next_x" : {},
    }

    lineIndex = 0
    lineCount = len(data)

    glyphCount_defined = 0
    glyphCount_found = 0
    width, height = 0, 0
    xOff, yOff = 0, 0

    while lineIndex < lineCount:
        line = data[lineIndex]

        # Detecting global font info

        if line.startswith("FONT "):
            font["name"] = line.removeprefix("FONT ")
        
        elif line.startswith("FONTBOUNDINGBOX "):
            width, height, xOff, yOff = (int(x) for x in line.removeprefix("FONTBOUNDINGBOX ").split())

        elif line.startswith("CHARS "):
            glyphCount_defined = int(line.removeprefix("CHARS "))

        elif line.startswith("STARTCHAR "):
            glyphName = line.removeprefix("STARTCHAR ")

            lineIndex2 = lineIndex + 1

            while lineIndex2 < lineCount:
                line2 = data[lineIndex2]

                if line2.startswith("ENCODING "):
                    encoding = int(line2.removeprefix("ENCODING "))
                    if encoding == -1: encoding = 1
                    glyph = chr(encoding)

                elif line2.startswith("BBX "):
                    glyphWidth, glyphHeight, glyphXOff, glyphYOff = (int(x) for x in line2.removeprefix("BBX ").split())

                elif line2.startswith("DWIDTH "):
                    dwX0, dwY0 = (int(x) for x in line2.removeprefix("DWIDTH ").split())

                elif line2.startswith("BITMAP"):
                    bitmap = ["."*(glyphXOff + glyphWidth) for _ in range(height)]
                    rowStart = height - glyphHeight - glyphYOff + yOff

                    rowData = []
                    binLength = len(data[lineIndex2 + 1].rstrip("\n")) * 4   # each hex digit = 4 binary digits
                    totalWidth = glyphWidth + glyphXOff

                    for i in range(glyphHeight):
                        line3 = data[lineIndex2 + 1 + i]

                        if line3.startswith("ENDCHAR"):
                            break

                        d = int(line3, 16)
                        s = format(d, f'0{binLength}b')
                        
                        processed = "."*(glyphXOff) + s
                        rowData.append(
                            processed[:max(totalWidth, binLength - glyphWidth + glyphXOff + 1)]
                            )

                    for i, row in enumerate(rowData):
                        try: bitmap[rowStart + i] = row.replace("0", ".")
                        except IndexError:
                            print(width, height, xOff, yOff, glyphWidth, glyphHeight, glyphXOff, glyphYOff, i)

                    font[glyph] = bitmap
                    font["next_x"][glyph] = dwX0 - (totalWidth)
                    glyphCount_found += 1

                elif line2.startswith("ENDCHAR"):
                    break

                lineIndex2 += 1

            lineIndex = lineIndex2

        elif line.startswith("ENDFONT"):
            if glyphCount_found == glyphCount_defined: 
                break
            else:
                raise InvalidBDFStructure(f"Font {font_dir} has different glyph count ({glyphCount_found}) than amount of actually defined glyphs ({glyphCount_defined}).")

        lineIndex += 1

    return font