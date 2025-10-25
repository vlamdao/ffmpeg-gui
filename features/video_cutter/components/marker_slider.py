from PyQt5.QtWidgets import QSlider, QStyleOptionSlider
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtCore import Qt

class MarkerSlider(QSlider):
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
        if self.maximum() == 0:
            return

        painter = QPainter(self)
        style = self.style()
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)

        # Draw existing segments
        pen = QPen(Qt.NoPen)
        brush = QBrush(Qt.blue, Qt.Dense4Pattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        for start_ms, end_ms in self.segment_markers:
            start_pos = int((start_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            end_pos = int((end_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawRect(start_pos, groove_rect.y(), end_pos - start_pos, groove_rect.height())

        # Draw current start marker
        if self.current_start_marker != -1:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            marker_pos = int((self.current_start_marker / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawLine(marker_pos, groove_rect.top(), marker_pos, groove_rect.bottom())