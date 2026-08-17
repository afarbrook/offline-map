import sys
from pathlib import Path
from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt, QPointF, QAbstractListModel, QModelIndex

import tile_source
import mapping_functions
import map_view
import flag


@dataclass 
class Placement:
    id: int  
    lat: float
    lon: float
    unit_id: str
    unit_type: str
    status: str
    created_at: str



class PlacementModel(QAbstractListModel):

    def __init__(self):
        super().__init__()
        self._placement = []
        self._nextID = 0


    def add(self, lat, lon, unit_id, unit_type, status, created_at):
        row = len(self._placement)
        self.beginInsertRows(QModelIndex(), row, row)
        placed = Placement(self._nextID, lat, lon, unit_id, unit_type, status, created_at)
        self._nextID += 1
        self._placement.append(placed)
        self.endInsertRows()
        return placed

    def remove(self, row):
        if not 0 <= row < len(self._placement):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._placement[row]
        self.endRemoveRows()

    def move(self, row, lat, lon):
        if not 0 <= row < len(self._placement):
                    return
        self._placement[row].lat = lat
        self._placement[row].lon = lon
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx)

    def rowCount(self, parent=QModelIndex()):
        return len(self._placement)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
             return None

        marker = self._placement[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return f"{marker.id}  {marker.unit_type}"
 
        if role == Qt.ItemDataRole.DecorationRole:
            pass
 
        if role == Qt.ItemDataRole.ToolTipRole:
            pass
 
        if role == Qt.ItemDataRole.UserRole:
            # your own data, invisible to the view -- e.g. a database id
            return marker
 
        return None

    def at(self, row):
         if  0 <= row < len(self._placement):
              return self._placement[row]
         return None

    def row_of_id(self, ID):
        for place in range(len(self._placement)):
            if self._placement[place].id == ID:
                return place
        return None
         

        


