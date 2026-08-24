import sys
from pathlib import Path
from dataclasses import dataclass
import csv

from PySide6.QtCore import QRectF, Qt, QModelIndex, QAbstractListModel

@dataclass
class Vehicle:
    unit_id: str
    unit_type: str
    status: str
    origin: str

class InventoryModel(QAbstractListModel):

    def __init__(self, path):

        super().__init__()
        self._fleet = []

        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                v = Vehicle(row["unit_id"], row["unit_type"], row["status"], row["origin"])
                self._fleet.append(v)

        


    def add(self, unit_id, unit_type, status, origin):
        new_vehicle = Vehicle(unit_id, unit_type, status, origin)
        self._fleet.append(new_vehicle)

    def get_next(self, unit_type="EN"):
        for vehicle in self._fleet:
            if vehicle.unit_type == unit_type and vehicle.status == "available":
                vehicle.status = "busy"
                return vehicle
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._fleet)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        vehicle = self._fleet[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return f"{vehicle.unit_id}  {vehicle.unit_type}"
    
        if role == Qt.ItemDataRole.DecorationRole:
            return 
    
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{vehicle.unit_type} — {vehicle.status}"
    
        if role == Qt.ItemDataRole.UserRole:
            # your own data, invisible to the view -- e.g. a database id
            return vehicle  
        return None
        