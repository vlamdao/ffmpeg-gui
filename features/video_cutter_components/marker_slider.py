from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor

_MARKER_COLOR = QColor(0, 120, 215, 100)

class MarkerSlider(QSlider):
    """A custom QSlider that can draw markers for video segments."""
    
    def __init__(self, orientation):
        super().__init__(orientation)
        self.segment_markers = [] # List of (start_ms, end_ms) tuples
        self.current_start_marker_ms = -1 # Single start_ms for the temporary marker

    def set_segment_markers(self, markers):
        """Sets the list of markers to be drawn."""
        self.segment_markers = markers
        self.update() # Trigger a repaint

    def set_current_start_marker(self, start_ms):
        """Sets the position of the temporary start marker."""
        self.current_start_marker_ms = start_ms
        self.update() # Trigger a repaint

    def paintEvent(self, event):
        """Override paintEvent to draw markers on the slider track."""
        super().paintEvent(event) # Draw the slider first

        painter = QPainter(self)
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)

        # Draw completed segment markers
        if self.segment_markers:
            painter.setBrush(_MARKER_COLOR) # Blue color for segments
            painter.setPen(Qt.NoPen)
            for start_ms, end_ms in self.segment_markers:
                start_pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), start_ms, groove_rect.width())
                end_pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), end_ms, groove_rect.width())
                marker_height = groove_rect.height()
                marker_rect = QRect(groove_rect.x() + start_pos, groove_rect.y(), end_pos - start_pos, marker_height)
                painter.drawRect(marker_rect)

        # Draw current start marker
        if self.current_start_marker_ms != -1:
            painter.setBrush(_MARKER_COLOR) # Red color for start marker
            painter.setPen(Qt.NoPen) # Red border
            start_pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), self.current_start_marker_ms, groove_rect.width())
            marker_width = 2 # A thin line
            marker_height = groove_rect.height()
            marker_rect = QRect(groove_rect.x() + start_pos - marker_width // 2, groove_rect.y(), marker_width, marker_height)
            painter.drawRect(marker_rect)

    def mousePressEvent(self, event):
        """Override mousePressEvent to allow jumping to a position by clicking on the groove."""
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
            handle_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            if groove_rect.contains(event.pos()) and not handle_rect.contains(event.pos()):
                pos_in_groove = event.pos().x() - groove_rect.x()
                value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos_in_groove, groove_rect.width())
                self.setValue(value)
                self.sliderReleased.emit()
        super().mousePressEvent(event)