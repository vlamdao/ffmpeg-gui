from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
from helper import resource_path
from typing import Optional


class StyledButton(QPushButton):
    def __init__(self,
                 text: str,
                 icon_name: Optional[str] = None,
                 icon_size: Optional[QSize] = None,
                 min_height: Optional[int] = None,
                 min_width: Optional[int] = None,
                 tooltip: Optional[str] = None,
                 padding: Optional[tuple[int, int, int, int]] = None,
                 layout_direction: Optional[Qt.LayoutDirection] = None,
                 parent=None):
        super().__init__(text)

        if icon_name:
            self.setIcon(QIcon(resource_path(f"icon/{icon_name}")))
        if icon_size:
            self.set_icon_size(icon_size)
        if min_width:
            self.set_min_width(min_width)
        if min_height:
            self.set_min_height(min_height)
        if tooltip:
            self.set_tooltip(tooltip)
        if padding:
            self.set_padding(padding)
        if layout_direction is not None:
            self.set_layout_direction(layout_direction)

    def set_padding(self, padding: tuple[int, int, int, int]):
        padding_left, padding_top, padding_right, padding_bottom = padding

        style_parts = []
        if padding_left != 0:
            style_parts.append(f"padding-left: {padding_left}px;")
        if padding_right != 0:
            style_parts.append(f"padding-right: {padding_right}px;")
        if padding_top != 0:
            style_parts.append(f"padding-top: {padding_top}px;")
        if padding_bottom != 0:
            style_parts.append(f"padding-bottom: {padding_bottom}px;")
        if style_parts:
            self.setStyleSheet(" ".join(style_parts))

    def set_layout_direction(self, layout_direction: Qt.LayoutDirection):
        self.setLayoutDirection(layout_direction)

    def set_icon(self, icon_name: str):
        self.setIcon(QIcon(resource_path(f"icon/{icon_name}")))

    def set_icon_size(self, icon_size: QSize):
        self.setIconSize(icon_size)

    def set_min_width(self, min_width: int):
        self.setMinimumWidth(min_width)

    def set_min_height(self, min_height: int):
        self.setMinimumHeight(min_height)

    def set_tooltip(self, tooltip: str):
        self.setToolTip(tooltip)