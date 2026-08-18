from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtWidgets import (
    QListView
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