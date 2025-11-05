from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

class Slider(QSlider):

    seek_requested = pyqtSignal(int)

    def __init__(self, orientation, parent=None):
        """Initializes the MarkerSlider."""
        super().__init__(orientation, parent)
        self._segment_markers = []
        self._current_start_marker = -1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
            self.setValue(value)
            self.seek_requested.emit(value)

        super().mousePressEvent(event)

    def set_segment_markers(self, segments):
        """Sets the list of segments to be painted on the slider.

        Args:
            segments (list[tuple[int, int]]): A list of (start_ms, end_ms) tuples.
        """
        self._segment_markers = segments
        self.update()

    def set_current_start_marker(self, position):
        """Sets the position of the temporary 'start' marker.

        Args:
            position (int): The position in milliseconds, or -1 to hide it.
        """
        self._current_start_marker = position
        self.update()

    def paintEvent(self, event):
        """Overrides the paint event to draw custom markers and segments."""
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
        color.setAlpha(128) # Set transparency (0-255)
        brush = QBrush(color, Qt.Dense4Pattern)

        painter.setPen(pen)
        painter.setBrush(brush)
        for start_ms, end_ms in self._segment_markers:
            start_pos = int((start_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            end_pos = int((end_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawRect(start_pos, groove_rect.y(), end_pos - start_pos, groove_rect.height())

        # Draw current start marker
        if self._current_start_marker != -1:
            pen = QPen(Qt.blue, 1)
            painter.setPen(pen)
            marker_pos = int((self._current_start_marker / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawLine(marker_pos, groove_rect.top(), marker_pos, groove_rect.bottom())
