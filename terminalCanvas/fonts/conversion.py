class UnsupportedFileTypeError(Exception):
    pass

class InvalidBDFStructure(Exception):
    pass

# ------------------------------
# BDF to Text-usable dict format
# ------------------------------

'''
More details on the Bitmap Distribution Format (BDF) can be found on
https://adobe-type-tools.github.io/font-tech-notes/pdfs/5005.BDF_Spec.pdf

Global font information:
- STARTFONT number          -> number defines version of file format
- COMMENT string            -> comments to ignore
- CONTENTVERSION integer    -> (opt.) version of content/data
- FONT string               -> PostScript(TM) language font name
- SIZE PointSize Xres Yres  -> point size & intended x, y res of device
- FONTBOUNDINGBOX FBBx FBBy x_off y_off   -> max width & max height, and x y displacement of lower left corner from 0
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
- VVECTOR x_off y_off         -> components of a vector from 0 to 1. Check the spec for better understanding.
- BBX BBw BBh BBx_off0x BBy_off0y         -> width BBw of black pixels in x, height BBh in y, and x y displacement.
- BITMAP (newline) <hexData>-> denote start of bitmap. hexData to represent pixel presence per line in hex (to bin: 1=pixel, 0=empty)
- ENDCHAR                   -> denote end of reading char
- ENDFONT                   -> denote end of reading font. error cond. if called before all glyphs have been read
'''

def from_bdf(font_dir: str) -> dict:
    """
    Read through a BDF font and convert it to a Python dict to be used with `Text`.

    Parameters:
    - font_dir: str

    Returns:
    - dict
    """

    if not font_dir.endswith(".bdf"):
        raise UnsupportedFileTypeError(f"Must be of type '.bdf' for this conversion.")

    with open(font_dir, "r", encoding="ascii") as font:
        data = [line.rstrip("\n") for line in font]

    font = {}

    line_index = 0
    line_count = len(data)

    global_width, global_height = 0, 0
    global_x_off, global_y_off = 0, 0

    while line_index < line_count:
        line = data[line_index]

        # Detecting global font info
        
        if line.startswith("FONTBOUNDINGBOX "):
            global_width, global_height, global_x_off, global_y_off = (int(x) for x in line.removeprefix("FONTBOUNDINGBOX ").split())

        elif line.startswith("STARTCHAR "):
            glyphName = line.removeprefix("STARTCHAR ") 

            encoding = None
            glyph = None
            glyph_width = glyph_height = 0
            glyph_x_off = glyph_y_off = 0
            dwX0 = dwY0 = 0

            line_index2 = line_index + 1

            while line_index2 < line_count:
                line2 = data[line_index2]

                if line2.startswith("ENCODING "):
                    raw_enc = line2.removeprefix("ENCODING ").split()
                    encoding = int(raw_enc[0] if len(raw_enc) == 1 else raw_enc[-1])

                    if encoding != -1:
                        glyph = chr(encoding)
                    #else:
                    #    glyph = f"unencoded:{glyphName}"

                elif line2.startswith("BBX "):
                    glyph_width, glyph_height, glyph_x_off, glyph_y_off = [int(x) for x in line2.removeprefix("BBX ").split()]

                elif line2.startswith("DWIDTH "):
                    dwX0, dwY0 = [int(x) for x in line2.removeprefix("DWIDTH ").split()]

                elif line2.startswith("BITMAP"):
                    bitmap = [" " * (glyph_x_off + glyph_width)] * height
                    row_start = height - glyph_height - glyph_y_off + y_off
                    total_width = glyph_width + glyph_x_off

                    next_line = data[line_index2 + 1] 
                    if next_line != "ENDCHAR":
                        row_data = []
                        binary_length = len(next_line) * 4   # each hex digit = 4 binary digits
                        
                        for i in range(glyph_height):
                            line3 = data[line_index2 + 1 + i] 

                            if line3.startswith("ENDCHAR"):
                                break

                            d = int(line3, 16)
                            s = format(d, f'0{binary_length}b').replace("0", " ")
                            
                            processed = " "*(glyph_x_off) + s
                            row_data.append(
                                processed[:max(total_width, binary_length - glyph_width + glyph_x_off)]
                                )

                        for i, row in enumerate(row_data):
                            try:
                                bitmap[row_start + i] = row
                            except IndexError:
                                raise InvalidBDFStructure(
                                    f"Failed while writing row {row_start + i} to glyph {glyph} whose row "
                                    f"indices are strictly in range [0, {height-1}]. This may be caused due "
                                    "to corrupted font or unconventional data formatting.\n"
                                    "For additional information, check the following metrics: "
                                    f"{global_width=}, {global_height=}, {global_x_off=}, {global_y_off=}, "
                                    f"{glyph_width=}, {glyph_height=}, {glyph_x_off=}, {glyph_y_off=}, "
                                    f"{height=}, {i=}, {row_start=}"
                                    )

                    font[glyph] = {"bitmap": bitmap}
                    next_x = dwX0 - total_width
                    if next_x != 0:
                        font[glyph]["next_x"] = next_x
                    if glyph_x_off < 0:
                        font[glyph]["offset_x"] = glyph_x_off

                elif line2.startswith("ENDCHAR"):
                    break

                line_index2 += 1

            line_index = line_index2

        elif line.startswith("ENDFONT"):
            break

        line_index += 1

    return font