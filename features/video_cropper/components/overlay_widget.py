from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, QEvent, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath


class OverlayWidget(QWidget):
    """
    A transparent, top-level widget used to draw a resizable crop rectangle
    over another widget (e.g., a video player) without being affected by
    the underlying widget's painting behavior (like VLC's airspace issue).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Make the widget a frameless, transparent, top-level window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)

        # --- Crop rectangle state management ---
        self._HANDLE_SIZE = 10
        self._crop_rect_geometry = QRect()
        self._is_resizing = False
        self._drag_start_pos = QPoint()
        self._drag_start_geom = QRect()
        self._resize_handle = None
        # -----------------------------------------

    def get_crop_geometry(self) -> QRect:
        """Returns the current geometry of the crop rectangle."""
        return self._crop_rect_geometry

    def showEvent(self, event):
        super().showEvent(event)
        # Initialize crop rectangle to be half the size of the widget and centered.
        if self._crop_rect_geometry.isNull():
            widget_rect = self.rect()
            new_width = widget_rect.width() // 2
            new_height = widget_rect.height() // 2
            new_x = (widget_rect.width() - new_width) // 2
            new_y = (widget_rect.height() - new_height) // 2
            self._crop_rect_geometry = QRect(new_x, new_y, new_width, new_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        border_color = QColor(Qt.yellow)

        # Draw the crop rectangle border. _crop_rect_geometry is the border itself.
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(border_color, 1, Qt.SolidLine))
        painter.drawRect(self._crop_rect_geometry.adjusted(0, 0, -1, -1))
        
        # Draw resize handles
        painter.setBrush(border_color)
        for handle_rect in self._get_handles(self._crop_rect_geometry).values():
            painter.drawRect(handle_rect)

    def _get_handles(self, rect: QRect):
        """Returns a dictionary of handle rectangles for the four corners."""
        # Handles are positioned completely outside the given rect.
        s = self._HANDLE_SIZE

        return {
            # Corners
            'top-left': QRect(rect.left() - s, rect.top() - s, s, s),
            'top-right': QRect(rect.right(), rect.top() - s, s, s),
            'bottom-left': QRect(rect.left() - s, rect.bottom(), s, s),
            'bottom-right': QRect(rect.right(), rect.bottom(), s, s),
        }

    def _get_handle_at(self, pos: QPoint):
        for handle, rect in self._get_handles(self._crop_rect_geometry).items():
            if rect.contains(pos):
                return handle
        return None

    def mousePressEvent(self, event):
        """Handles mouse clicks to start or stop resizing."""
        if event.button() == Qt.LeftButton:
            # If already in resizing mode, this click will stop it.
            if self._is_resizing:
                self._is_resizing = False
                self._resize_handle = None
            # Otherwise, check if a handle is clicked to start resizing.
            else:
                handle = self._get_handle_at(event.pos())
                if handle:
                    self._is_resizing = True
                    self._resize_handle = handle
                    self._drag_start_pos = event.globalPos()
                    self._drag_start_geom = QRect(self._crop_rect_geometry)

    def mouseMoveEvent(self, event):
        """Handles mouse movement for resizing or updating the cursor."""
        if self._is_resizing:
            # If resizing, update the geometry based on mouse movement.
            delta = event.globalPos() - self._drag_start_pos
            new_geom = QRect(self._drag_start_geom)

            if 'top' in self._resize_handle: new_geom.setTop(new_geom.top() + delta.y())
            if 'bottom' in self._resize_handle: new_geom.setBottom(new_geom.bottom() + delta.y())
            if 'left' in self._resize_handle: new_geom.setLeft(new_geom.left() + delta.x())
            if 'right' in self._resize_handle: new_geom.setRight(new_geom.right() + delta.x())
            
            new_geom = new_geom.normalized()
            self._crop_rect_geometry = new_geom.intersected(self.rect().adjusted(self._HANDLE_SIZE, self._HANDLE_SIZE, -self._HANDLE_SIZE, -self._HANDLE_SIZE))
            self.update()

    def mouseReleaseEvent(self, event):
        """This event is now ignored in the click-move-click model."""
        pass

    def setEnabled(self, enabled):
        """Override setEnabled to also reset the resizing state."""
        super().setEnabled(enabled)
        if not enabled:
            # If the widget is disabled (e.g., during processing), exit resizing mode.
            if self._is_resizing:
                self._is_resizing = True
