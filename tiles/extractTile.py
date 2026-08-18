"""
Pull one tile out of an .mbtiles file and save it as a standalone .png so you
can open it in a normal image viewer -- one that shows transparency as a
checkerboard, not flattened to white.

Windows Photos / Paint will NOT show transparency correctly (they flatten to
white, which is exactly the ambiguity we're trying to resolve). Use:
  - GIMP (free)
  - VS Code (hover/open the png -- its preview shows a checkerboard)
  - A browser: drag the .png into a new tab

Usage:
    python extract_tile.py <mbtiles_file> <z> <x> <y>

Example, using the UA campus tile from earlier in this project:
    python extract_tile.py test.mbtiles 16 12570 26563

If you don't know a good z/x/y to try, run with no arguments and it will
pick and extract the first tile it finds in the file.
"""

import sqlite3
import sys
from pathlib import Path

MBTILES_PATH = Path(__file__).parent / "tucson.mbtiles"

def extract(mbtiles_path, z=None, x=None, y=None):
    con = sqlite3.connect(mbtiles_path)

    if z is None:
        # no coordinates given -- just grab whatever tile comes first
        row = con.execute(
            "SELECT zoom_level, tile_column, tile_row, tile_data "
            "FROM tiles LIMIT 1"
        ).fetchone()
        if row is None:
            print("No tiles found in this file.")
            return
        z, tms_x, tms_y, data = row
        xyz_y = (2**z - 1) - tms_y
        print(f"(no z/x/y given -- picked the first tile: "
              f"z{z} x{tms_x} y{xyz_y})")
    else:
        tms_y = (2**z - 1) - y  # XYZ -> TMS, same flip as the app uses
        row = con.execute(
            "SELECT tile_data FROM tiles "
            "WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, tms_y),
        ).fetchone()
        if row is None:
            print(f"No tile at z{z} x{x} y{y} in this file.")
            print("Check the tile is actually in the render's bbox/zoom range")
            print("-- run check_mbtiles.py on this file to see what IS there.")
            return
        data = row[0]
        tms_x = x

    # sniff the format from the file's own magic bytes, rather than trusting
    # the metadata table (which can be wrong if the render used a different
    # format than it claims)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        ext = "png"
    elif data[:2] == b"\xff\xd8":
        ext = "jpg"
    else:
        ext = "bin"
        print("Warning: unrecognised image header -- saving raw bytes anyway.")

    out = Path(mbtiles_path).with_name(f"tile_z{z}_x{tms_x}_y{y or ''}.{ext}")
    out.write_bytes(data)

    print(f"wrote {out}  ({len(data):,} bytes, format={ext})")
    print(f"open it in something that renders transparency as a checkerboard")
    print(f"-- if the tile is actually transparent where you expect a dark")
    print(f"background, you'll see the checkerboard there, not white.")


if __name__ == "__main__":
    extract(MBTILES_PATH)