import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QColor

class test(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))

class rectangle(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.r1 = QRect(100, 200, 11, 16)
        

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor("blue"))       # Border color
        painter.setBrush(QColor("lightblue")) # Inside color
        
        # Display the rectangle visually
        painter.drawRect(self.r1)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = rectangle()
    widget.resize(800, 600)
    widget.show()


    sys.exit(app.exec())