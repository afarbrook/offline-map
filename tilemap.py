"""
Tile map -- skeleton.

This is the file that becomes your application. The scaffolding is here and
runs; the two functions that make it a map are left for you, marked TODO.

Run it as-is and you get an empty scrollable canvas the size of Tucson, with a
status bar showing which tiles *should* be loaded. Fill in the TODOs and tiles
appear.

Run:  python tilemap.py
"""
import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QPushButton, 
    QGraphicsRectItem, 
    QWidget, 
    QVBoxLayout,
    QDockWidget
)

import tile_source
import mapping_functions
import map_view
import flag

MBTILES_PATH = Path(__file__).parent / "./tiles/tucson.mbtiles"

TILE = 256
ZOOM = 16

# Tucson bbox at z16, from the projection work. x 12542-12615, y 26538-26602.
BBOX_TILES = (12542, 26538, 12615, 26602)

# Somewhere to start looking -- UA campus.
START_LAT, START_LON = 32.2319, -110.9501


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tucson tile map")
        self.resize(1280, 720)

        self.source = tile_source.TileSource(MBTILES_PATH)

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

        self.view = map_view.TileMapView(scene, self.source, self)
        self.setCentralWidget(self.view)

        # Start centred on somewhere real rather than the corner of the bbox.
        wx, wy = mapping_functions.latlon_to_world(START_LAT, START_LON, ZOOM)
        self.view.centerOn(wx, wy)
        self.view.refresh_tiles()

        self.statusBar().showMessage("Drag to pan, scroll to zoom.")

        self.dock = QDockWidget("Test", self)

        self.toolbar = QWidget(self)
        
        # 2. Set up a vertical layout inside the container
        layout = QVBoxLayout(self.toolbar)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.btn_select = QPushButton("Select Mode")
        self.btn_draw = QPushButton("Draw Mode")
        self.btn_clear = QPushButton("Clear All")
        
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_draw)
        layout.addWidget(self.btn_clear)

        content_widget = QWidget()
        content_widget.setLayout(layout)
        self.dock.setWidget(content_widget)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)


    def closeEvent(self, event):
        self.source.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
