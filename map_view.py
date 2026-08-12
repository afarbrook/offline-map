from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsView,
    QWidget, 
    QVBoxLayout
)
from mapping_functions import world_to_latlon, latlon_to_world
import flag


TILE = 256
ZOOM = 16

# Tucson bbox at z16, from the projection work. x 12542-12615, y 26538-26602.
BBOX_TILES = (12542, 26538, 12615, 26602)

# Somewhere to start looking -- UA campus.
START_LAT, START_LON = 32.2319, -110.9501

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
        self._panStart = None

        self.setScene(self._scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
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
        if self._panStart:
            deltaPos = event.position() - self._panStart
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - deltaPos.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - deltaPos.y())
            self._panStart = event.position()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._panStart = None
        self.unsetCursor()
        return super().mouseReleaseEvent(event)

    def _update_status(self):
        win = self.window()
        if hasattr(win, "statusBar"):
            n = len(self.visible_tile_keys())
            win.statusBar().showMessage(
                f"want {n} tiles, have {len(self._tiles)} in scene"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panStart = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton:
            self.map_clicked()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            selected = self._scene.selectedItems()
            for pin in selected:
                self._scene.removeItem(pin)

        return super().keyPressEvent(event)

    def map_clicked():
        
        pass
# ---------------------------------------------------------------------------
