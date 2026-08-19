from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtWidgets import (
    QPushButton, 
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)

class UnitPushButton(QPushButton):


    def __init__(self, letter, name, subtitle, color, unit_type, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setProperty("unit_type", unit_type)
        self.setMinimumSize(165, 50)
        badge = QLabel(letter)
        badge.setFixedSize(32, 32)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {color}; color: white; "
            f"border-radius: 4px; font-weight: bold;"
        )

        title = QLabel(name)
        title.setStyleSheet("font-weight: bold; color: #e0e0e0;")

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setStyleSheet("color: #888888; font-size: 11px;")

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.addWidget(title)
        text_col.addWidget(subtitle_lbl)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)   # this is now your ONLY spacing
        layout.setSpacing(8)    
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text_col)
        layout.addStretch()


