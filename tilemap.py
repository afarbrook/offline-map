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
    QListView,
    QButtonGroup,
    QGridLayout,
    QLabel
)

from PySide6.QtGui import QColor

import tile_source
import mapping_functions
import flag
import map_view
from model import PlacementModel
import placement_list_view
from unit_buttons import UnitPushButton

MBTILES_PATH = Path(__file__).parent / "./tiles/tucson.mbtiles"
STYLE_PATH = Path(__file__).parent / "./style/styleSheet.qss"

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
        dock = QDockWidget(self)

        dock.setTitleBarWidget(title)
        dock.setWidget(self.panel)
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
            f = flag.flag(x, y, self.panel.current_unit_type())
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
        for row in range(topLeft.row(), bottomRight.row() + 1):
            placed = self.model.at(row)
            f = self._pins.get(placed.id)
            print(1)
            if f is None:
                continue
            wx, wy = mapping_functions.latlon_to_world(placed.lat, placed.lon, ZOOM)
            f.setPos(wx, wy)

    def on_map_clicked(self, lat, lon):
        unit_type = self.panel.current_unit_type()
        if unit_type is not None:
            self.model.add(lat, lon , 5, unit_type, 5, 5)

    def on_flag_deleted(self, id):
        row = self.model.row_of_id(id)
        if row is not None:
            self.model.remove(row)

    



class PlacementPanel(QWidget):

    unit_type_selected = Signal(str)
    clear_requested = Signal()
    pin_deleted = Signal(int)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

        self.unit_list = placement_list_view.PlacementListView()
        self.unit_list.setModel(model)
        self.unit_list.setMaximumHeight(500)
        
        
        # 2. Set up a vertical layout inside the container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        '''
        self.btn_select = QPushButton("Select Mode")
        self.btn_draw = QPushButton("Draw Mode")
        '''
        self.create_buttons()
        self.unit_group = QButtonGroup(self)
        self.unit_group.addButton(self.btn_engine)
        self.unit_group.addButton(self.btn_assistant_chief)
        self.unit_group.addButton(self.btn_crash_truck)
        self.unit_group.addButton(self.btn_tender)
        self.unit_group.addButton(self.btn_light_squad)
        self.unit_group.addButton(self.btn_fire_chief)
        self.unit_group.addButton(self.btn_paramedic)
        self.unit_group.addButton(self.btn_ladder)
        self.unit_group.addButton(self.btn_SUV)

        self.btn_clear.clicked.connect(self.clear_requested.emit)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        grid.addWidget(self.btn_engine, 0, 0)
        grid.addWidget(self.btn_assistant_chief, 0, 1)
        grid.addWidget(self.btn_crash_truck, 0 , 2)
        grid.addWidget(self.btn_tender, 1, 0)
        grid.addWidget(self.btn_light_squad, 1, 1)
        grid.addWidget(self.btn_fire_chief, 1, 2)
        grid.addWidget(self.btn_paramedic, 2, 0)
        grid.addWidget(self.btn_ladder, 2, 1)
        grid.addWidget(self.btn_SUV, 2, 2)

        subtitle = QLabel("PLACE UNIT — CLICK TYPE, THEN MAP")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            f"color: #7b7f85; "
            f"border-radius: 10px; border-color: white;"
            f"font-size: 12px; qproperty-alignment: 'AlignLeft'"
    
        )

        text = QLabel("DEPLOYED UNITS")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet(
            f"color: #7b7f85; "
            f"border-radius: 4px;"
            f"font-size: 12px; qproperty-alignment: 'AlignLeft'"
    
        )

        layout.addWidget(subtitle)
        layout.addLayout(grid)
        layout.addWidget(text)
        layout.addWidget(self.unit_list, stretch=1)
        

        layout.addStretch()

        self.unit_list.selectionModel().selectionChanged.connect(self.on_list_selection)
        self.unit_list.pin_deleted.connect(self.pin_deleted.emit)

    def current_unit_type(self):
        btn = self.unit_group.checkedButton()
        return btn.property("unit_type") if btn else None

    def on_list_selection(self):
        indexes = self.unit_list.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            placement = self.model.at(row)

    def create_buttons(self):
        self.btn_clear = QPushButton("Clear All")
                
        self.btn_engine = UnitPushButton("EN", "Engine", "TFD · TRUCK", "#e04736", "EN")
        self.btn_engine.setCheckable(True)
        self.btn_engine.setProperty("unit_type", "EN")
        self.btn_engine.setChecked(True)

        self.btn_paramedic = UnitPushButton("PM", "Paramedic", "TFD · BOX", "#517adb", "PM")
        self.btn_paramedic.setCheckable(True)
        self.btn_paramedic.setProperty("unit_type", "PM")

        self.btn_SUV = UnitPushButton("RE", "SUV", "TPD · SUV", "#13ccaa", "RE")
        self.btn_SUV.setCheckable(True)
        self.btn_SUV.setProperty("unit_type", "RE")

        self.btn_ladder = UnitPushButton("LD", "Ladder", "TFD · LD", "#cc8813", "LD")
        self.btn_ladder.setCheckable(True)
        self.btn_ladder.setProperty("unit_type", "LD")

        self.btn_light_squad = UnitPushButton("LQ", "Light Squad", "TPD · SUV", "#b8c0b8", "LQ")
        self.btn_light_squad.setCheckable(True)
        self.btn_light_squad.setProperty("unit_type", "LQ")

        self.btn_fire_chief = UnitPushButton("FC", "Fire Chief", "TFD · SEDAN", "#8269ce", "FC")
        self.btn_fire_chief.setCheckable(True)
        self.btn_fire_chief.setProperty("unit_type", "FC")

        self.btn_tender = UnitPushButton("TN", "Tender", "TFD · SEDAN", "#d06fd3", "TN")
        self.btn_tender.setCheckable(True)
        self.btn_tender.setProperty("unit_type", "TN")

        self.btn_crash_truck = UnitPushButton("CR", "Crash Truck", "TPD · TRUCK", "#bad61d", "CR")
        self.btn_crash_truck.setCheckable(True)
        self.btn_crash_truck.setProperty("unit_type", "CR")  

        self.btn_assistant_chief = UnitPushButton("AC", "Asst. Chief", "TFD · SEDAN", "#1dd62d", "AC")
        self.btn_assistant_chief.setCheckable(True)
        self.btn_assistant_chief.setProperty("unit_type", "AC")


        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open(STYLE_PATH) as f:
        app.setStyleSheet(f.read())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
