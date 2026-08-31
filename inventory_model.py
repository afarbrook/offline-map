import sys
from pathlib import Path
from dataclasses import dataclass
import csv

from PySide6.QtCore import QRectF, Qt, QModelIndex, QAbstractTableModel

@dataclass
class Vehicle:
    unit_id: str
    unit_type: str
    status: str
    origin: str

class InventoryModel(QAbstractTableModel):
    COLUMNS = ["unit_id", "unit_type", "status", "origin"]
    def __init__(self, path):
        
        super().__init__()
        self._fleet = []

        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                v = Vehicle(row["unit_id"], row["unit_type"], row["status"], row["origin"])
                self._fleet.append(v)

        
    def rowCount(self, parent=QModelIndex()):
        return len(self._vehicles)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def add(self, unit_id, unit_type, status, origin):
        new_vehicle = Vehicle(unit_id, unit_type, status, origin)
        self._fleet.append(new_vehicle)

    def get_next(self, unit_type="EN"):
        for vehicle in self._fleet:
            if vehicle.unit_type == unit_type and vehicle.status == "AVAILABLE":
                vehicle.status = "busy"
                return vehicle
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._fleet)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        v = self._vehicles[index.row()]
        col = self.COLUMNS[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            return getattr(v, col)
        if role == Qt.ItemDataRole.UserRole:
            return v
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section].replace("_", " ").title()
        return None

    def __str__(self):
        return str(self._fleet)
        