from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

class SeekSlider(QSlider):
    """
    A custom QSlider that immediately jumps to the clicked position.

    This slider overrides the default mouse press behavior. When a user
    clicks anywhere on the slider's groove with the left mouse button,
    the slider's value is instantly set to that position, providing a
    "seek" functionality. This is different from the standard QSlider
    behavior which might require dragging the handle.
    """
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def mousePressEvent(self, event):
        """
        Handles the mouse press event to jump to the clicked position.

        Calculates the slider value corresponding to the mouse click's
        x-coordinate and sets the slider to that value.

        Args:
            event (QMouseEvent): The mouse press event.
        """
        if event.button() == Qt.LeftButton:
            value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
            self.setValue(value)

        super().mousePressEvent(event)

class MarkerSlider(SeekSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.segment_markers = []
        self.current_start_marker = -1

    def set_segment_markers(self, segments):
        self.segment_markers = segments
        self.update()

    def set_current_start_marker(self, position):
        self.current_start_marker = position
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.maximum() == 0: return # Avoid division by zero

        painter = QPainter(self)
        style = self.style()
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)

        # Draw existing segments
        pen = QPen(Qt.NoPen)
        color = QColor(Qt.blue)
        color.setAlpha(128) # Đặt độ trong suốt (0-255)
        brush = QBrush(color, Qt.Dense4Pattern)

        painter.setPen(pen)
        painter.setBrush(brush)
        for start_ms, end_ms in self.segment_markers:
            start_pos = int((start_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            end_pos = int((end_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawRect(start_pos, groove_rect.y(), end_pos - start_pos, groove_rect.height())

        # Draw current start marker
        if self.current_start_marker != -1:
            pen = QPen(Qt.blue, 1)
            painter.setPen(pen)
            marker_pos = int((self.current_start_marker / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawLine(marker_pos, groove_rect.top(), marker_pos, groove_rect.bottom())