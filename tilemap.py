"""
Tile map -- skeleton.

This is the file that becomes your application. The scaffolding is here and
runs; the two functions that make it a map are left for you, marked TODO.

Run it as-is and you get an empty scrollable canvas the size of Tucson, with a
status bar showing which tiles *should* be loaded. Fill in the TODOs and tiles
appear.

Run:  python tilemap.py
"""

import numpy as np
import sqlite3
import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap, QBrush, QColor
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QGraphicsEllipseItem,
    QGraphicsItem
)

MBTILES_PATH = Path(__file__).parent / "./tiles/tucson.mbtiles"

TILE = 256
ZOOM = 16

# Tucson bbox at z16, from the projection work. x 12542-12615, y 26538-26602.
BBOX_TILES = (12542, 26538, 12615, 26602)

# Somewhere to start looking -- UA campus.
START_LAT, START_LON = 32.2319, -110.9501


# ---------------------------------------------------------------------------
# projection -- replace with an import of your own verified module
# ---------------------------------------------------------------------------


def world_to_latlon(x, y, z):
    px, py = int(x / 256), int(y / 256)
    n = 2**z
    lon = (px/n) * 360 - 180
    lat = np.degrees( np.arctan( np.sinh(np.pi-(py/n)*(2*np.pi)) ) )
    return lat, lon

def latlon_to_world(lat, lon, z):
    n = 2**z
    xtile = ((lon + 180) / 360) * n
    ytile = ( 1- ( np.log (np.tan(np.radians(lat)) + (1/np.cos(np.radians(lat))) ) )/np.pi) * (n/2)
    return xtile*256, ytile*256


# ---------------------------------------------------------------------------
# tile source -- knows about SQLite and PNGs, knows nothing about Qt geometry
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# view
# ---------------------------------------------------------------------------


class TileMapView(QGraphicsView):
    MIN_SCALE = 0.25
    MAX_SCALE = 8.0
    ZOOM_STEP = 1.15

    # Load one extra ring of tiles beyond the viewport so they don't pop in
    # at the edge while panning.
    PAD = 1

    def __init__(self, scene, source, parent=None):
        super().__init__(parent)

        # These must exist BEFORE setScene(): setScene fires scrollContentsBy
        # synchronously, which calls refresh_tiles(), which reads both.
        self.source = source
        self._tiles = {}  # (z, x, y) -> QGraphicsPixmapItem currently in scene

        self._scene = scene  # keep a reference or it gets garbage collected
        self.setScene(self._scene)

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.viewport().setMouseTracking(True)

    # -- TODO 1 -------------------------------------------------------------

    def visible_tile_keys(self):
        """Return the set of (z, x, y) keys that should be loaded right now.
        """
        visableRegion = self.mapToScene(self.viewport().rect()).boundingRect() #converts view coordinates into scene coordinates
        tx0 = int(visableRegion.left()//TILE) - self.PAD
        ty0 = int(visableRegion.top()//TILE) - self.PAD
        tx1 = int(visableRegion.right()//TILE) + self.PAD
        ty1 = int(visableRegion.bottom()//TILE) + self.PAD

        return {(ZOOM, x, y)
                for x in range(tx0, tx1 + 1)
                for y in range(ty0, ty1 + 1)}

    # -- TODO 2 -------------------------------------------------------------

    def refresh_tiles(self):
        """Add tiles that entered the viewport, remove ones that left.
        """
        wanted = self.visible_tile_keys()
        loaded = set(self._tiles)
        for key in wanted - loaded:
            pm = self.source.get(*key)
            if pm:
                x = key[1]
                y = key[2]
                item = QGraphicsPixmapItem(pm)
                item.setPos(x * TILE, y * TILE)
                item.setZValue(-1)
                self._scene.addItem(item)
                self._tiles[key] = item

        for key in loaded - wanted:
            self._scene.removeItem(self._tiles.pop(key))

        self._update_status()

    # -- events that change what's visible ----------------------------------

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)  # let Qt scroll first, then react
        self.refresh_tiles()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_tiles()

    def wheelEvent(self, event):
        factor = self.ZOOM_STEP if event.angleDelta().y() > 0 else 1 / self.ZOOM_STEP
        target = self.transform().m11() * factor
        if target < self.MIN_SCALE or target > self.MAX_SCALE:
            return
        self.scale(factor, factor)
        self.refresh_tiles()

    # -- status readout -----------------------------------------------------

    def mouseMoveEvent(self, event):
        pt = self.mapToScene(event.position().toPoint())
        lat, lon = world_to_latlon(pt.x(), pt.y(), ZOOM)
        win = self.window()
        if hasattr(win, "statusBar"):
            win.statusBar().showMessage(
                f"{lat:.5f}, {lon:.5f}     "
                f"tile {int(pt.x() // TILE)}/{int(pt.y() // TILE)}     "
                f"loaded: {len(self._tiles)}"
            )
        super().mouseMoveEvent(event)

    def _update_status(self):
        win = self.window()
        if hasattr(win, "statusBar"):
            n = len(self.visible_tile_keys())
            win.statusBar().showMessage(
                f"want {n} tiles, have {len(self._tiles)} in scene"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.pos())
            f = flag(int(scene_pos.x()), int(scene_pos.y()))
            self.scene().addItem(f)
        super().mousePressEvent(event)
# ---------------------------------------------------------------------------
# flag class for constant item on screen
class flag(QGraphicsEllipseItem):

    def __init__(self, wx, wy):
        super().__init__(-6, -6, 12, 12)
        self.setPos(wx, wy)
        self.setBrush(QBrush(QColor("#c0392b")))
        self.setZValue(1)                              
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self._lat, self._lon = world_to_latlon(wx, wy, ZOOM)
        

    def setLatlon(self, wx, wy): 
        self._lat, self._lon = world_to_latlon(wx, wy, ZOOM)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tucson tile map")
        self.resize(1000, 700)

        self.source = TileSource(MBTILES_PATH)

        scene = QGraphicsScene()
        x0, y0, x1, y1 = BBOX_TILES
        scene.setSceneRect(
            QRectF(
                x0 * TILE,
                y0 * TILE,
                (x1 - x0 + 1) * TILE,
                (y1 - y0 + 1) * TILE,
            )
        )

        self.view = TileMapView(scene, self.source, self)
        self.setCentralWidget(self.view)

        # Start centred on somewhere real rather than the corner of the bbox.
        wx, wy = latlon_to_world(START_LAT, START_LON, ZOOM)
        self.view.centerOn(wx, wy)
        self.view.refresh_tiles()

        #TEST CODE REMOVE IN PROD
        eclipse = flag(wx, wy)
        scene.addItem(eclipse)

        self.statusBar().showMessage("Drag to pan, scroll to zoom.")


    def closeEvent(self, event):
        self.source.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
