"""
Minimal QGraphicsView pan + zoom demo.

Three rectangles in a scene. Drag to pan, scroll to zoom.
The status bar shows the scene coordinate under your cursor -- that readout
is the same mechanic you'll later use to turn a click into a lat/lon.

Run:  python panzoom_demo.py
"""

import sys

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
)


class PanZoomView(QGraphicsView):
    """A view that pans by dragging and zooms toward the cursor on scroll."""

    # Clamp the zoom so you can't scroll into oblivion in either direction.
    MIN_SCALE = 0.05
    MAX_SCALE = 20.0

    ZOOM_STEP = 1.15  # multiplier per wheel notch

    def __init__(self, scene, parent=None):
        super().__init__(parent)

        # IMPORTANT: QGraphicsView does not take ownership of the scene.
        # If nothing on the Python side holds a reference, the scene is garbage
        # collected the moment this constructor returns and you get a blank,
        # silent, error-free white widget. Keep the reference explicitly.
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
                f"scene: {pt.x():8.1f}, {pt.y():8.1f}    "
                f"zoom: {self.transform().m11():.3f}x"
            )

        super().mouseMoveEvent(event)  # let ScrollHandDrag still do its job


def build_scene():
    scene = QGraphicsScene()

    # Scene coordinates are arbitrary and unbounded. Later, yours will be
    # Web Mercator pixels at your max zoom level.
    scene.setSceneRect(QRectF(-500, -500, 1000, 1000))

    specs = [
        (-300, -200, 250, 180, "#c0392b"),
        (-50, 0, 300, 200, "#2980b9"),
        (100, -300, 150, 150, "#27ae60"),
    ]

    for x, y, w, h, color in specs:
        item = QGraphicsRectItem(x, y, w, h)
        item.setBrush(QBrush(QColor(color)))
        item.setPen(QPen(QColor("#2c3e50"), 2))
        scene.addItem(item)

    # A crosshair at the origin, so you can see the scene isn't moving --
    # the view is.
    scene.addLine(-40, 0, 40, 0, QPen(QColor("#7f8c8d"), 1))
    scene.addLine(0, -40, 0, 40, QPen(QColor("#7f8c8d"), 1))

    return scene


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pan / Zoom demo")
        self.resize(900, 650)

        self.view = PanZoomView(build_scene(), self)
        self.setCentralWidget(self.view)

        self.statusBar().showMessage("Drag to pan, scroll to zoom.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())