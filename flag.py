from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsSimpleTextItem
)
from mapping_functions import world_to_latlon, latlon_to_world


TILE = 256
ZOOM = 16
UNIT_COLORS = {"EN": QColor("#e04736"), "PM": QColor("#517adb"),
               "LD": QColor("#cc8813"), "RE": QColor("#13ccaa"), 
               "AC": QColor("#1dd62d"), "CR": QColor("#bad61d"),
               "TN": QColor("#d06fd3"), "LQ": QColor("#b8c0b8"),
               "FC": QColor("#8269ce")
            }
# flag class for constant item on screen
class flag(QGraphicsEllipseItem):

    

    def __init__(self, wx, wy, type="engine"):
        super().__init__(-6, -6, 18, 18)
        self.label = QGraphicsSimpleTextItem(type, self)
        rect = self.label.boundingRect()
        self.label.setPos(3-rect.width() / 2, 3-rect.height() / 2)
        self.setPos(wx, wy)
        self.setBrush(QBrush(UNIT_COLORS[type]))
        self.setZValue(1)                              
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True
        )
        self._lat, self._lon = world_to_latlon(wx, wy, ZOOM)

   

    def setLatlon(self, wx, wy): 
        self._lat, self._lon = world_to_latlon(wx, wy, ZOOM)

    def itemChange(self, change, value):
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
            and self.scene()
        ):
            new_pos = value
            grid_size = 30 

            
            x = new_pos.x()
            y = new_pos.y()

            return QPointF(x, y)  # Return the snapped coordinates

        return super().itemChange(change, value)