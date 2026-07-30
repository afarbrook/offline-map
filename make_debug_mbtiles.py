"""
Generate a synthetic MBTiles file of labeled debug tiles for Tucson.

This is scaffolding, not part of your app -- it exists so you can build and
debug the map canvas today instead of waiting on QGIS or your GIS team.

Each tile is a flat color with its own z/x/y printed on it and a border drawn
around the edge. That makes three classes of bug immediately visible:

  * y-flip wrong      -> tile labels count in the wrong direction vertically
  * range math off    -> gaps or a stripe of missing tiles at the edges
  * placement wrong   -> borders don't line up into a clean grid

Writes tiles in TMS row order, exactly like a real MBTiles file, so your
reader has to get the flip right.

Usage:
    pip install pillow
    python make_debug_mbtiles.py
    -> tucson_debug.mbtiles
"""

import math
import sqlite3
import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

# --- config -----------------------------------------------------------------

BBOX = (-111.10, 32.05, -110.70, 32.35)  # w, s, e, n  -- City of Tucson
MIN_ZOOM = 10
MAX_ZOOM = 16
TILE = 256
OUT = "tucson_debug.mbtiles"

# --- projection -------------------------------------------------------------


def deg2num(lat, lon, z):
    """lat/lon -> fractional tile coordinates."""
    n = 2.0**z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


# --- tile drawing -----------------------------------------------------------


def _font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT_BIG = _font(28)
FONT_SMALL = _font(18)

# Checkerboard so adjacent tiles are visually distinct.
PALETTE = [(232, 240, 247), (247, 240, 232)]


def make_tile(z, x, y):
    """Render one debug tile as PNG bytes. x/y are XYZ (not TMS)."""
    bg = PALETTE[(x + y) % 2]
    img = Image.new("RGB", (TILE, TILE), bg)
    d = ImageDraw.Draw(img)

    # border -- lets you see tile seams and confirm alignment
    d.rectangle([0, 0, TILE - 1, TILE - 1], outline=(120, 140, 160), width=1)

    # crosshair at tile center
    c = TILE // 2
    d.line([c - 8, c, c + 8, c], fill=(180, 190, 200), width=1)
    d.line([c, c - 8, c, c + 8], fill=(180, 190, 200), width=1)

    d.text((12, 10), f"z{z}", font=FONT_BIG, fill=(60, 80, 100))
    d.text((12, 48), f"x {x}", font=FONT_SMALL, fill=(90, 110, 130))
    d.text((12, 72), f"y {y}", font=FONT_SMALL, fill=(90, 110, 130))

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# --- mbtiles ----------------------------------------------------------------


def build():
    if os.path.exists(OUT):
        os.remove(OUT)

    con = sqlite3.connect(OUT)
    cur = con.cursor()
    cur.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
    cur.execute(
        "CREATE TABLE tiles ("
        "  zoom_level INTEGER,"
        "  tile_column INTEGER,"
        "  tile_row INTEGER,"
        "  tile_data BLOB)"
    )

    w, s, e, n = BBOX
    for k, v in [
        ("name", "Tucson debug tiles"),
        ("type", "baselayer"),
        ("version", "1.0"),
        ("description", "Synthetic labeled tiles for canvas development"),
        ("format", "png"),
        ("bounds", f"{w},{s},{e},{n}"),
        ("minzoom", str(MIN_ZOOM)),
        ("maxzoom", str(MAX_ZOOM)),
    ]:
        cur.execute("INSERT INTO metadata VALUES (?, ?)", (k, v))

    total = 0
    for z in range(MIN_ZOOM, MAX_ZOOM + 1):
        x0, y0 = deg2num(n, w, z)  # NW corner
        x1, y1 = deg2num(s, e, z)  # SE corner
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)

        count = 0
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                # MBTiles stores rows bottom-up (TMS). This is the flip your
                # reader has to undo: y_xyz = (2**z - 1) - y_tms
                tms_y = (2**z - 1) - y
                cur.execute(
                    "INSERT INTO tiles VALUES (?, ?, ?, ?)",
                    (z, x, tms_y, make_tile(z, x, y)),
                )
                count += 1
        total += count
        print(f"  z{z:<3} x {x0}-{x1}  y {y0}-{y1}   {count:>6,} tiles")

    # The index a real MBTiles file has; your SELECT will hit it.
    cur.execute(
        "CREATE UNIQUE INDEX tile_index ON tiles "
        "(zoom_level, tile_column, tile_row)"
    )
    con.commit()
    con.close()

    size = os.path.getsize(OUT) / 1024 / 1024
    print(f"\nwrote {OUT}  --  {total:,} tiles, {size:.1f} MB")


if __name__ == "__main__":
    build()
