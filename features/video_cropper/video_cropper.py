from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QMessageBox, QGraphicsView,
                             QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem,
                             QApplication, QRubberBand, QGroupBox, QFormLayout,
                             QLineEdit, QLabel)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter

from helper import resource_path
from components import PlaceholdersTable
from .processor import VideoCropperProcessor
from .components import (ActionPanel, CommandTemplate, VideoCropperPlaceholders)

import subprocess
import sys

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger

class CroppingView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPointF()

    def set_pixmap(self, pixmap):
        self.scene().clear()
        self.scene().addPixmap(pixmap)
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        self.origin = self.mapToScene(event.pos())
        self.rubber_band.setGeometry(QRect(event.pos(), QSize()))
        self.rubber_band.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.rubber_band.setGeometry(QRect(self.mapToScene(self.origin).toPoint(), event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.rubber_band.hide()
        rect = self.rubber_band.geometry()
        scene_rect = self.mapToScene(rect).boundingRect()
        self.parent().update_crop_parameters(scene_rect)
        super().mouseReleaseEvent(event)

class VideoCropper(QDialog):
    def __init__(self, video_path: str, output_folder: str, logger: 'Logger', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Cropper")
        self.setWindowIcon(QIcon(resource_path("icon/crop-video.png")))
        self.setMinimumSize(800, 600)

        self._video_path = video_path
        self._output_folder = output_folder
        self._logger = logger
        self._placeholders = VideoCropperPlaceholders()
        self._processor = VideoCropperProcessor(self)

        self._setup_ui()
        self._connect_signals()
        self._load_first_frame()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.scene = QGraphicsScene(self)
        self.view = CroppingView(self.scene, self)
        
        self.crop_params_group = QGroupBox("Crop Parameters")
        form_layout = QFormLayout()
        self.width_edit = QLineEdit()
        self.height_edit = QLineEdit()
        self.x_edit = QLineEdit()
        self.y_edit = QLineEdit()
        form_layout.addRow(QLabel("Width:"), self.width_edit)
        form_layout.addRow(QLabel("Height:"), self.height_edit)
        form_layout.addRow(QLabel("X:"), self.x_edit)
        form_layout.addRow(QLabel("Y:"), self.y_edit)
        self.crop_params_group.setLayout(form_layout)

        self._placeholders_table = PlaceholdersTable(
            placeholders_list=self._placeholders.get_placeholders_list(),
            num_columns=6,
            parent=self
        )
        self._placeholders_table.set_compact_height()

        self._cmd_template = CommandTemplate(placeholders=self._placeholders)
        self._action_panel = ActionPanel()

        main_layout.addWidget(self.view)
        main_layout.addWidget(self.crop_params_group)
        main_layout.addWidget(self._placeholders_table)
        main_layout.addWidget(self._cmd_template)
        main_layout.addWidget(self._action_panel)

    def _connect_signals(self):
        self._action_panel.run_clicked.connect(self._start_crop_process)
        self._action_panel.stop_clicked.connect(self._stop_crop_process)
        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)
        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)

    def _load_first_frame(self):
        try:
            command = [
                'ffmpeg', '-i', self._video_path, '-vframes', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'
            ]
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            image_data = pipe.stdout.read()
            pipe.terminate()

            if image_data:
                image = QImage.fromData(image_data)
                pixmap = QPixmap.fromImage(image)
                self.view.set_pixmap(pixmap)
            else:
                QMessageBox.warning(self, "Error", "Could not load the first frame of the video.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to extract frame: {e}")

    def update_crop_parameters(self, rect: QRectF):
        self.width_edit.setText(str(int(rect.width())))
        self.height_edit.setText(str(int(rect.height())))
        self.x_edit.setText(str(int(rect.x())))
        self.y_edit.setText(str(int(rect.y())))

    def _start_crop_process(self):
        crop_params = {
            'w': self.width_edit.text(), 'h': self.height_edit.text(),
            'x': self.x_edit.text(), 'y': self.y_edit.text()
        }
        self._action_panel.update_ui_state('disable')
        self._processor.start(self._video_path, self._output_folder, self._cmd_template, crop_params)

    def _stop_crop_process(self):
        self._processor.stop()

    @pyqtSlot()
    def _on_processing_finished(self):
        self._action_panel.update_ui_state('enable')