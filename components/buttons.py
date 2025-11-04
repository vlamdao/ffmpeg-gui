from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
from helper import resource_path
from typing import Optional


class StyledButton(QPushButton):
    def __init__(self,
                 text: str,
                 icon_name: str,
                 icon_size: QSize,
                 min_height: int,
                 tooltip: Optional[str] = None,
                 padding: Optional[tuple[int, int, int, int]] = None,
                 layout_direction: Optional[Qt.LayoutDirection] = None,
                 parent=None):
        super().__init__(text)
        self.setIcon(QIcon(resource_path(f"icon/{icon_name}")))
        self.setIconSize(icon_size)
        self.setMinimumHeight(min_height)

        if tooltip:
            self.setToolTip(tooltip)
        if padding:
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

        if layout_direction is not None:
            self.setLayoutDirection(layout_direction)
