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

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QMainWindow,
    QPushButton, 
    QWidget, 
    QVBoxLayout,
    QDockWidget,
    QListView
)

import tile_source
import mapping_functions
import flag
import map_view
from model import PlacementModel

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
        self._pins = {}
        self.source = tile_source.TileSource(MBTILES_PATH)
        self.model = PlacementModel()

        self.scene = QGraphicsScene()
        x0, y0, x1, y1 = BBOX_TILES
        self.scene.setSceneRect(
            QRectF(
                x0 * TILE,
                y0 * TILE,
                (x1 - x0 + 1) * TILE,
                (y1 - y0 + 1) * TILE,
            )
        )

        self.view = map_view.TileMapView(self.scene, self.source, self)
        self.setCentralWidget(self.view)

        # Start centred on somewhere real rather than the corner of the bbox.
        wx, wy = mapping_functions.latlon_to_world(START_LAT, START_LON, ZOOM)
        self.view.centerOn(wx, wy)
        self.view.refresh_tiles()

        
        self.panel = PlacementPanel(self.model)
        dock = QDockWidget("Placements", self)
        dock.setWidget(self.panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        self.model.rowsInserted.connect(self.on_rows_inserted)
        self.model.rowsAboutToBeRemoved.connect(self.on_rows_removed)
        self.model.dataChanged.connect(self.on_data_changed)
        self.view.map_clicked.connect(self.on_map_clicked)
        self.view.pin_deleted.connect(self.on_flag_deleted)

        self.statusBar().showMessage("Drag to pan, scroll to zoom.")



    def closeEvent(self, event):
        self.source.close()
        super().closeEvent(event)

    def on_rows_inserted(self, parent, first, last):
        for row in range(first, last + 1):
            placed = self.model.at(row)
            x, y = mapping_functions.latlon_to_world(placed.lat, placed.lon, ZOOM)
            f = flag.flag(x, y)
            f.setData(0, placed.id)
            self.scene.addItem(f)
            self._pins[placed.id] = f # add to our own record

    def on_rows_removed(self, parent, first, last):
        for row in range(first, last + 1):
            placed = self.model.at(row)
            f = self._pins[placed.id]
            self.scene.removeItem(f)
            self._pins[placed.id] = None

    def on_data_changed(self, topLeft, bottomRight, roles=None):
        pass

    def on_map_clicked(self, lat, lon):
        unit_type = self.panel.current_unit_type()
        if unit_type is not None:
            self.model.add(lat, lon , 5, unit_type, 5, 5)

    def on_flag_deleted(self, id):
        row = self.model.row_of_id(id)
        if row:
            self.model.remove(row)



class PlacementPanel(QWidget):

    unit_type_selected = Signal(str)
    clear_requested = Signal()

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

        self.unit_list = QListView()
        self.unit_list.setModel(model)
        

        # 2. Set up a vertical layout inside the container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.btn_select = QPushButton("Select Mode")
        self.btn_draw = QPushButton("Draw Mode")
        self.btn_clear = QPushButton("Clear All")
        self.btn_test = QPushButton("Test")
        self.btn_test.setCheckable(True)
        self.btn_test.setProperty("unit_type", "engine")


        self.btn_clear.clicked.connect(self.clear_requested.emit)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_draw)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.unit_list)
        layout.addWidget(self.btn_test)

        layout.addStretch()

    def current_unit_type(self):
        return self.btn_test.property("unit_type")

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
