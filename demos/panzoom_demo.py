"""
Reference demo: pan + zoom over a single map tile.

This file is deliberately finished and frozen. It proves the whole bottom of
the stack works -- SQLite read, TMS y-flip, PNG decode, scene placement -- and
nothing more. Keep it runnable so that when the real app misbehaves you have a
known-good baseline to compare against.

Drag to pan, scroll to zoom. The status bar shows the scene coordinate under
the cursor.

Run:  python panzoom_demo.py
"""

import sqlite3
import sys

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
)

MBTILES_PATH = "tucson_debug.mbtiles"
TILE = 256

# One tile over the UA campus, verified against the projection test suite.
DEMO_Z, DEMO_X, DEMO_Y = 16, 12570, 26563


class PanZoomView(QGraphicsView):
    """A view that pans by dragging and zooms toward the cursor on scroll."""

    # Clamp the zoom so you can't scroll into oblivion in either direction.
    MIN_SCALE = 0.05
    MAX_SCALE = 20.0

    ZOOM_STEP = 1.15  # multiplier per wheel notch

    def __init__(self, scene, parent=None):
        super().__init__(parent)

        # QGraphicsView does not take ownership of the scene. If nothing on the
        # Python side holds a reference, the scene is garbage collected the
        # moment this constructor returns and you get a blank, silent,
        # error-free white widget. Keep the reference explicitly.
        self._scene = scene
        self.setScene(self._scene)

        # Left-drag pans the view. Qt handles the scrollbar math for us.
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # THE important line: zoom keeps the point under the mouse fixed.
        # Without this, scale() zooms toward the view's center and feels wrong.
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Resizing the window shouldn't yank the view around.
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Continuous cursor updates without a button held down. Note this goes
        # on the VIEWPORT, not the view -- QGraphicsView is a scroll area, and
        # setting it on the view itself silently does nothing.
        self.viewport().setMouseTracking(True)

    # -- zoom ---------------------------------------------------------------

    def wheelEvent(self, event):
        # angleDelta is in eighths of a degree; sign is all we care about.
        if event.angleDelta().y() > 0:
            factor = self.ZOOM_STEP
        else:
            factor = 1 / self.ZOOM_STEP

        # current uniform scale factor, read off the view's transform
        current = self.transform().m11()
        target = current * factor

        if target < self.MIN_SCALE or target > self.MAX_SCALE:
            return  # refuse the zoom rather than clamping mid-gesture

        self.scale(factor, factor)

    # -- cursor readout -----------------------------------------------------

    def mouseMoveEvent(self, event):
        # mapToScene converts widget pixels -> scene coordinates.
        # This is the exact call you'll wrap to get lat/lon from a click.
        pt = self.mapToScene(event.position().toPoint())

        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(
                f"scene: {pt.x():12,.1f}, {pt.y():12,.1f}    "
                f"zoom: {self.transform().m11():.3f}x"
            )

        super().mouseMoveEvent(event)  # let ScrollHandDrag still do its job


def build_scene():
    """A scene containing exactly one tile, placed at its true world position."""
    scene = QGraphicsScene()

    con = sqlite3.connect(MBTILES_PATH)

    # MBTiles stores rows bottom-up (TMS); slippy-map convention is top-down
    # (XYZ). Flip before querying or you get None.
    tms_y = (2**DEMO_Z - 1) - DEMO_Y

    row = con.execute(
        "SELECT tile_data FROM tiles "
        "WHERE zoom_level=? AND tile_column=? AND tile_row=?",
        (DEMO_Z, DEMO_X, tms_y),
    ).fetchone()
    con.close()

    if row is None:
        raise SystemExit(
            f"tile {DEMO_Z}/{DEMO_X}/{DEMO_Y} not found in {MBTILES_PATH}.\n"
            "Run make_debug_mbtiles.py first, and check you're running from "
            "the same directory as the .mbtiles file."
        )

    pm = QPixmap()
    pm.loadFromData(row[0])

    item = QGraphicsPixmapItem(pm)
    # The georeferencing: tile 12570 starts at world pixel 12570 * 256.
    item.setPos(DEMO_X * TILE, DEMO_Y * TILE)
    item.setZValue(-1)  # tiles paint below everything else
    scene.addItem(item)

    # Scene coordinates here are in the millions, so the scrollable region has
    # to be set explicitly -- the default would leave the view pointed at empty
    # space near the origin.
    scene.setSceneRect(item.sceneBoundingRect())
    return scene


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pan / zoom demo -- one tile")
        self.resize(900, 650)

        self.view = PanZoomView(build_scene(), self)
        self.setCentralWidget(self.view)

        self.statusBar().showMessage("Drag to pan, scroll to zoom.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
