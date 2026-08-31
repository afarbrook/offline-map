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
    QTableView
)

from PySide6.QtGui import QColor

import tile_source
import mapping_functions
import flag
import map_view
from model import PlacementModel
from inventory_model import InventoryModel
import views
from unit_buttons import UnitPushButton

class PlacementPanel(QWidget):

    unit_type_selected = Signal(str)
    clear_requested = Signal()
    pin_deleted = Signal(int)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

        self.unit_list = views.PlacementListView()
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


class InventoryPanel(QWidget):

    vehicle_selected = Signal(str)
    def __init__(self, model, parent=None):
        super().__init__(parent)
        
        self.inventory_model = model
        self.inventory_view = views.InventoryTableView()
        self.inventory_view.setModel(self.inventory_model)
        self.inventory_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.inventory_view.setSortingEnabled(True)
        self.inventory_view.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        layout.addWidget(self.inventory_view)

        self.inventory_view.vehicle_selected.connect(self.vehicle_selected)
        
        
        

    