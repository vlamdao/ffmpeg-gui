from PyQt5.QtWidgets import QWidget, QRubberBand
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal

class ResizableRectangle(QWidget):
    """
    A draggable and resizable rectangle overlay widget.

    This widget provides visual handles for resizing and can be moved.
    It emits a signal whenever its geometry changes.
    """
    geometry_changed = pyqtSignal(QRect)

    _HANDLE_SIZE = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._is_resizing = False
        self._is_moving = False
        self._drag_start_pos = QPoint()
        self._drag_start_geom = QRect()
        self._resize_handle = None

    def _get_handles(self):
        """Returns a dictionary of handle rectangles."""
        s = self._HANDLE_SIZE
        w, h = self.width(), self.height()
        return {
            'top-left': QRect(0, 0, s, s),
            'top-right': QRect(w - s, 0, s, s),
            'bottom-left': QRect(0, h - s, s, s),
            'bottom-right': QRect(w - s, h - s, s, s),
            'top': QRect(s, 0, w - 2 * s, s),
            'bottom': QRect(s, h - s, w - 2 * s, s),
            'left': QRect(0, s, s, h - 2 * s),
            'right': QRect(w - s, s, s, h - 2 * s),
        }

    def _get_handle_at(self, pos):
        """Finds which handle is at a given position."""
        for handle, rect in self._get_handles().items():
            if rect.contains(pos):
                return handle
        return None

    def set_geometry(self, rect: QRect):
        """Sets the widget's geometry and emits the changed signal."""
        if rect != self.geometry():
            self.setGeometry(rect)
            self.geometry_changed.emit(rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw main rectangle border
        border_color = QColor(Qt.yellow)
        painter.setPen(QPen(border_color, 1, Qt.SolidLine)) # 1px is the thinnest possible
        painter.setBrush(Qt.NoBrush) # Make the inside transparent
        # Draw rect adjusted by 1px to stay inside the widget boundaries
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resize_handle = self._get_handle_at(event.pos())
            self._drag_start_pos = event.globalPos()
            self._drag_start_geom = self.geometry()

            if self._resize_handle:
                self._is_resizing = True
            else:
                self._is_moving = True

    def mouseMoveEvent(self, event):
        pos = event.pos()
        handle = self._get_handle_at(pos)

        # Update cursor
        if (self._is_resizing and self._resize_handle in ['top-left', 'bottom-right']) or \
           (handle in ['top-left', 'bottom-right']):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (self._is_resizing and self._resize_handle in ['top-right', 'bottom-left']) or \
             (handle in ['top-right', 'bottom-left']):
            self.setCursor(Qt.SizeBDiagCursor)
        elif (self._is_resizing and self._resize_handle in ['top', 'bottom']) or \
             (handle in ['top', 'bottom']):
            self.setCursor(Qt.SizeVerCursor)
        elif (self._is_resizing and self._resize_handle in ['left', 'right']) or \
             (handle in ['left', 'right']):
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)

        # Perform move or resize
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self._drag_start_pos
            new_geom = QRect(self._drag_start_geom)

            if self._is_moving:
                new_geom.translate(delta)
            elif self._is_resizing:
                if 'top' in self._resize_handle:
                    new_geom.setTop(new_geom.top() + delta.y())
                if 'bottom' in self._resize_handle:
                    new_geom.setBottom(new_geom.bottom() + delta.y())
                if 'left' in self._resize_handle:
                    new_geom.setLeft(new_geom.left() + delta.x())
                if 'right' in self._resize_handle:
                    new_geom.setRight(new_geom.right() + delta.x())

            # Normalize the rectangle if width/height becomes negative
            new_geom = new_geom.normalized()

            # Constrain within parent boundaries
            if self.parent():
                parent_rect = self.parent().rect()
                new_geom.setLeft(max(new_geom.left(), parent_rect.left()))
                new_geom.setRight(min(new_geom.right(), parent_rect.right()))
                new_geom.setTop(max(new_geom.top(), parent_rect.top()))
                new_geom.setBottom(min(new_geom.bottom(), parent_rect.bottom()))

            self.setGeometry(new_geom)
            self.geometry_changed.emit(new_geom)

    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        self._is_moving = False
        self._resize_handle = None
        self.setCursor(Qt.ArrowCursor)

    def resizeEvent(self, event):
        """Ensure the widget is repainted on resize."""
        self.update()
        super().resizeEvent(event)