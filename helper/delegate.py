from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QStyleOptionViewItem
from typing import Optional

class FontDelegate(QStyledItemDelegate):
    """
    A delegate to customize the font of items in a view.

    This delegate allows setting a specific font family and/or size for
    items in a QAbstractItemView (like QTableWidget or QListView).
    It modifies the existing font of the item, preserving other
    attributes like weight or style.
    """
    def __init__(self, font_family: Optional[str] = None, font_size: Optional[int] = None, parent=None):
        """
        Initializes the FontDelegate.

        Args:
            font_family (Optional[str]): The font family to apply. Defaults to None.
            font_size (Optional[int]): The font size to apply. Defaults to None.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        super().__init__(parent)
        self.font_family = font_family
        self.font_size = font_size

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        """
        Initializes the style option for the item at the given index.

        This method is called by the view to get the style options for painting
        an item. We override it to apply our custom font settings.

        Args:
            option (QStyleOptionViewItem): The style option to be initialized.
            index (QModelIndex): The model index of the item being painted.
        """
        super().initStyleOption(option, index)
        if self.font_family is not None:
            option.font.setFamily(self.font_family)
        if self.font_size is not None:
            option.font.setPointSize(self.font_size)
