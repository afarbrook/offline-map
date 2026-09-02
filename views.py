from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QListView,
    QTableView
)

class PlacementListView(QListView):
    pin_deleted = Signal(int)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            indexes = self.selectedIndexes()
            if indexes:
                placement = self.model().at(indexes[0].row())
                self.pin_deleted.emit(placement.id)
        else:
            super().keyPressEvent(event)

class InventoryTableView(QTableView):
    vehicle_selected = Signal(str)   # unit_id

    def __init__(self):
        super().__init__()
        self.selectionModel_connected = False

    def setModel(self, model):
        super().setModel(model)
        self.selectionModel().selectionChanged.connect(self._on_selection)

    def _on_selection(self):
        indexes = self.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            vehicle = self.model().data(self.model().index(row, 0), Qt.ItemDataRole.UserRole)
            self.vehicle_selected.emit(vehicle.unit_id)