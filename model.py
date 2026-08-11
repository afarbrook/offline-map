import sys
from pathlib import Path
from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt, QPointF, QAbstractListModel, QModelIndex

import tile_source
import mapping_functions
import map_view
import flag

class PlacementModel(QAbstractListModel):

    def __init__(self):
        super().__init__()
        self._placement = []


    def add(self, lat, lon, unit_id, unit_type, status, created_at):
        row = len(self._placement)
        self.beginInsertRows(QModelIndex(), row, row)
        placed = Placement(row, lat, lon, unit_id, unit_type, status, created_at)
        self._placement.append(placed)
        self.endInsertRows()

    def remove(self, row):
        if not 0 <= row <= len(self._placement):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._items[row]
        self.endRemoveRows()

    def move(self, row, lat, lon):
        if not 0 <= row <= len(self._placement):
                    return
        self._placement[row].lat = lat
        self._placement[row].lon = lon
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx)

    def rowCount(self):
        return len(self._placement)

    def data(self, index, role):
        if not index.isValid():
             return None

        marker = self._placement[index.row()]

        #TODO
        pass


@dataclass
class Placement:
    id: int
    lat: float
    lon: float
    unit_id: str
    unit_type: str
    status: str
    created_at: str

