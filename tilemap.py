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

from PySide6.QtCore import QRectF, Qt, Signal, QPointF
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QMainWindow,
    QPushButton, 
    QWidget, 
    QVBoxLayout,
    QDockWidget,
    QListView,
    QButtonGroup,
    QGridLayout,
    QLabel,
    QTabWidget
)

from PySide6.QtGui import QColor

import tile_source
import mapping_functions
import flag
import map_view
import time
from model import PlacementModel
from inventory_model import InventoryModel
import views
from unit_buttons import UnitPushButton
from panels import PlacementPanel, InventoryPanel

MBTILES_PATH = Path(__file__).parent / "./tiles/tucson.mbtiles"
STYLE_PATH = Path(__file__).parent / "./style/styleSheet.qss"
INVENTORY_PATH = Path(__file__).parent / "inventory.csv"

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
        self.resize(1600,900)
        self._pins = {}
        self.source = tile_source.TileSource(MBTILES_PATH)
        self.model = PlacementModel()
        self.inventory_model = InventoryModel(INVENTORY_PATH)
        

        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QColor("#14171b"))
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

        title = QLabel("CAD / UNIT PLACEMENT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: white; padding-left: 1px; padding-top: 5px;"
            f"border-radius: 10px; border-color: white;"
            f"font-size: 18px; qproperty-alignment: 'AlignLeft'"
    
        )
        
        self.panel = PlacementPanel(self.model)

        self.inventory_panel = InventoryPanel(self.inventory_model)

        tabs = QTabWidget()
        tabs.addTab(self.panel, "Units")
        tabs.addTab(self.inventory_panel, "Inventory")
        dock = QDockWidget(self)

        dock.setTitleBarWidget(title)
        dock.setWidget(tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)



        self.model.rowsInserted.connect(self.on_rows_inserted)
        self.model.rowsAboutToBeRemoved.connect(self.on_rows_removed)
        self.model.dataChanged.connect(self.on_data_changed)
        self.view.map_clicked.connect(self.on_map_clicked)
        self.view.pin_deleted.connect(self.on_flag_deleted)
        self.panel.pin_deleted.connect(self.on_flag_deleted)

        self.statusBar().showMessage("Drag to pan, scroll to zoom.")



    def closeEvent(self, event):
        self.source.close()
        super().closeEvent(event)

    def on_rows_inserted(self, parent, first, last):
        for row in range(first, last + 1):
            placed = self.model.at(row)
            x, y = mapping_functions.latlon_to_world(placed.lat, placed.lon, ZOOM)
            f = flag.flag(x, y, self.on_moved, placed.id, self.panel.current_unit_type())
            f.setData(0, placed.id) 
            self.scene.addItem(f)
            self._pins[placed.id] = f # add to our own record

    def on_rows_removed(self, parent, first, last):
        for row in range(first, last + 1):
            placed = self.model.at(row)
            f = self._pins[placed.id]
            self.scene.removeItem(f)
            del self._pins[placed.id]

    def on_data_changed(self, topLeft, bottomRight, roles=None):
        for row in range(topLeft.row(), bottomRight.row() + 1):
            placed = self.model.at(row)
            f = self._pins.get(placed.id)
            if f is None:
                continue
            wx, wy = mapping_functions.latlon_to_world(placed.lat, placed.lon, ZOOM)
            if f.pos() != QPointF(wx, wy):
                f.setPos(wx, wy)

    def on_map_clicked(self, lat, lon):
        unit_type = self.panel.current_unit_type()
        if unit_type is not None:
            next_unit = self.inventory_model.get_next(unit_type)
            if next_unit is None:
                return
            self.model.add(lat, lon , next_unit.unit_id, unit_type, 5, time.time())

    def on_flag_deleted(self, id):
        row = self.model.row_of_id(id)
        if row is not None:
            self.model.remove(row)

    def on_moved(self, id, lat, lon):
        row = self.model.row_of_id(id)

        self.model.move(row, lat, lon)
        

    

    


        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open(STYLE_PATH) as f:
        app.setStyleSheet(f.read())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
