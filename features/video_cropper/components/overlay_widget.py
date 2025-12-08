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
        self._HANDLE_SIZE = 2
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
        # Initialize crop rectangle to cover the whole widget area
        if self._crop_rect_geometry.isNull():
            self._crop_rect_geometry = self.rect()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        border_color = QColor(Qt.yellow)
        
        # Draw semi-transparent overlay outside the crop rectangle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        full_rect = self.rect()
        path = QPainterPath()
        path.setFillRule(Qt.OddEvenFill)
        path.addRect(QRectF(full_rect))
        path.addRect(QRectF(self._crop_rect_geometry))
        painter.drawPath(path)

        # Draw the crop rectangle border
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(border_color, 1, Qt.SolidLine))
        painter.drawRect(self._crop_rect_geometry.adjusted(0, 0, -1, -1))

        # Draw resize handles
        painter.setBrush(border_color)
        for handle_rect in self._get_handles(self._crop_rect_geometry).values():
            painter.drawRect(handle_rect)

    def _get_handles(self, rect: QRect):
        """Returns a dictionary of handle rectangles."""
        s = self._HANDLE_SIZE
        w, h = rect.width(), rect.height()
        return {
            'top-left': QRect(rect.left(), rect.top(), s, s),
            'top-right': QRect(rect.right() - s, rect.top(), s, s),
            'bottom-left': QRect(rect.left(), rect.bottom() - s, s, s),
            'bottom-right': QRect(rect.right() - s, rect.bottom() - s, s, s),
            'top': QRect(rect.left() + s, rect.top(), w - 2 * s, s),
            'bottom': QRect(rect.left() + s, rect.bottom() - s, w - 2 * s, s),
            'left': QRect(rect.left(), rect.top() + s, s, h - 2 * s),
            'right': QRect(rect.right() - s, rect.top() + s, s, h - 2 * s),
        }

    def _get_handle_at(self, pos: QPoint):
        for handle, rect in self._get_handles(self._crop_rect_geometry).items():
            if rect.contains(pos):
                return handle
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resize_handle = self._get_handle_at(event.pos())
            self._drag_start_pos = event.globalPos()
            self._drag_start_geom = QRect(self._crop_rect_geometry)
            if self._resize_handle:
                self._is_resizing = True

    def mouseMoveEvent(self, event):
        # Chỉ thực hiện thay đổi kích thước nếu đang trong trạng thái resizing
        if self._is_resizing and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self._drag_start_pos
            new_geom = QRect(self._drag_start_geom)

            if self._resize_handle:
                if 'top' in self._resize_handle: new_geom.setTop(new_geom.top() + delta.y())
                if 'bottom' in self._resize_handle: new_geom.setBottom(new_geom.bottom() + delta.y())
                if 'left' in self._resize_handle: new_geom.setLeft(new_geom.left() + delta.x())
                if 'right' in self._resize_handle: new_geom.setRight(new_geom.right() + delta.x())

            new_geom = new_geom.normalized()
            self._crop_rect_geometry = new_geom.intersected(self.rect())
            self.update()
        else:
            # Cập nhật hình dạng con trỏ chuột khi di chuột qua các handle
            pos = event.pos()
            handle = self._get_handle_at(pos)
            if handle in ['top-left', 'bottom-right']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif handle in ['top-right', 'bottom-left']:
                self.setCursor(Qt.SizeBDiagCursor)
            elif handle in ['top', 'bottom']:
                self.setCursor(Qt.SizeVerCursor)
            elif handle in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_resizing = False
            self._resize_handle = None
            self.setCursor(Qt.ArrowCursor)
