import sqlite3

from PySide6.QtGui import QPixmap

class TileSource:
    """Reads tiles from an MBTiles file and caches the decoded pixmaps."""

    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self._cache = {}

    def get(self, z, x, y):
        """Return a QPixmap for the XYZ tile, or None if it isn't in the file."""
        key = (z, x, y)
        if key in self._cache:
            return self._cache[key]

        # MBTiles rows are bottom-up (TMS); ours are top-down (XYZ).
        tms_y = (2**z - 1) - y

        row = self.con.execute(
            "SELECT tile_data FROM tiles "
            "WHERE zoom_level=? AND tile_column=? AND tile_row=?",
            (z, x, tms_y),
        ).fetchone()

        if row is None:
            self._cache[key] = None  # remember the miss; don't re-query
            return None

        pm = QPixmap()
        pm.loadFromData(row[0])
        self._cache[key] = pm
        return pm

    def close(self):
        self.con.close()