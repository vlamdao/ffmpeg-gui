from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QFont

class FontDelegate(QStyledItemDelegate):
    def __init__(self, font_family=None, font_size=None, parent=None):
        super().__init__(parent)
        self.font_family = font_family
        self.font_size = font_size

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        font = option.font
        if self.font_family is not None:
            font.setFamily(self.font_family)
        if self.font_size is not None:
            font.setPointSize(self.font_size)
        option.font = font

