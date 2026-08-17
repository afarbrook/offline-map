from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem
)
from mapping_functions import world_to_latlon, latlon_to_world


TILE = 256
ZOOM = 16

# flag class for constant item on screen
class flag(QGraphicsEllipseItem):

    colors = {"engine": QBrush(QColor("#c0392b")), "ambulance": QBrush(QColor("#3a589d")),
               "ladder": QBrush(QColor("#cc8813")), "SUV/K9": QBrush(QColor("#13ccaa")), 
               "cruiser": QBrush(QColor("#1dd62d")) 
            }

    def __init__(self, wx, wy, type="engine"):
        super().__init__(-6, -6, 12, 12)
        self.setPos(wx, wy)
        self.setBrush(self.colors[type])
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