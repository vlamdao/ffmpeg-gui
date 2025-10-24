import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QSlider, QListWidget, QWidget, QStyle,
                             QMessageBox, QLabel, QListWidgetItem, QSizePolicy)
from PyQt5.QtCore import Qt, QUrl, QTime
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

class VideoCutterDialog(QDialog):
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Video Cutter")
        self.setMinimumSize(800, 600)
        self.video_path = video_path
        self.segments = []
        self.start_time = None
        self._media_loaded = False

        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        if not self._media_loaded:
            if os.path.exists(self.video_path):
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_path)))
                self.play_button.setEnabled(True)
                self._media_loaded = True
                self.media_player.play()
            else:
                QMessageBox.critical(self, "Error", f"Video file not found:\n{self.video_path}")
                self.play_button.setEnabled(False)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Video display
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setMinimumHeight(300)
        main_layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # Media controls
        media_controls = QWidget()
        controls_layout = QHBoxLayout(media_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setEnabled(False)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)

        self.time_label = QLabel("00:00:00 / 00:00:00")

        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.time_label)
        main_layout.addWidget(media_controls)

        # Segment definition
        segment_controls = QWidget()
        segment_layout = QHBoxLayout(segment_controls)
        segment_layout.setContentsMargins(0, 0, 0, 0)

        self.set_start_button = QPushButton("Set Start")
        self.set_end_button = QPushButton("Set End")
        self.add_segment_button = QPushButton("Add Segment")
        self.clear_segments_button = QPushButton("Clear List")

        self.start_label = QLabel("Start: --:--:--")
        self.end_label = QLabel("End: --:--:--")

        segment_layout.addWidget(self.set_start_button)
        segment_layout.addWidget(self.start_label)
        segment_layout.addWidget(self.set_end_button)
        segment_layout.addWidget(self.end_label)
        segment_layout.addStretch()
        segment_layout.addWidget(self.add_segment_button)
        segment_layout.addWidget(self.clear_segments_button)
        main_layout.addWidget(segment_controls)

        # Segment list
        self.segment_list = QListWidget()
        main_layout.addWidget(self.segment_list)

        # Action buttons
        action_buttons = QWidget()
        action_layout = QHBoxLayout(action_buttons)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.addStretch()
        self.cut_button = QPushButton("Cut Segments")
        self.cancel_button = QPushButton("Cancel")
        action_layout.addWidget(self.cut_button)
        action_layout.addWidget(self.cancel_button)
        main_layout.addWidget(action_buttons)

    def _connect_signals(self):
        self.play_button.clicked.connect(self.toggle_play)
        self.cancel_button.clicked.connect(self.reject)

        self.media_player.stateChanged.connect(self.update_media_state)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

        self.position_slider.sliderMoved.connect(self.set_position)

        self.set_start_button.clicked.connect(self.set_start_time)
        self.set_end_button.clicked.connect(self.set_end_time)
        self.add_segment_button.clicked.connect(self.add_segment)
        self.clear_segments_button.clicked.connect(self.clear_segments)

        self.cut_button.clicked.connect(self.process_cut)

    def ms_to_time_str(self, ms):
        time = QTime(0, 0, 0).addMSecs(ms)
        return time.toString("HH:mm:ss.zzz")[:-4]

    # Media Player Slots
    def toggle_play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def update_media_state(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def update_position(self, position):
        self.position_slider.setValue(position)
        duration = self.media_player.duration()
        self.time_label.setText(f"{self.ms_to_time_str(position)} / {self.ms_to_time_str(duration)}")

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)
        position = self.media_player.position()
        self.time_label.setText(f"{self.ms_to_time_str(position)} / {self.ms_to_time_str(duration)}")

    def set_position(self, position):
        self.media_player.setPosition(position)

    # Segment Handling Slots
    def set_start_time(self):
        self.start_time = self.media_player.position()
        self.start_label.setText(f"Start: {self.ms_to_time_str(self.start_time)}")

    def set_end_time(self):
        self.end_time = self.media_player.position()
        self.end_label.setText(f"End: {self.ms_to_time_str(self.end_time)}")

    def add_segment(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                QMessageBox.warning(self, "Invalid Segment", "End time must be after start time.")
                return
            
            segment = (self.start_time, self.end_time)
            self.segments.append(segment)
            
            start_str = self.ms_to_time_str(self.start_time)
            end_str = self.ms_to_time_str(self.end_time)
            
            item = QListWidgetItem(f"Segment {len(self.segments)}: {start_str} -> {end_str}")
            self.segment_list.addItem(item)

            # Reset for next segment
            self.start_time = None
            self.end_time = None
            self.start_label.setText("Start: --:--:--")
            self.end_label.setText("End: --:--:--")
        else:
            QMessageBox.warning(self, "Incomplete Segment", "Please set both start and end times.")

    def clear_segments(self):
        self.segments.clear()
        self.segment_list.clear()

    # Processing Slots
    def process_cut(self):
        if not self.segments:
            QMessageBox.warning(self, "No Segments", "Please add at least one segment to cut.")
            return

        output_path = self.parent.output_path.get_completed_output_path(os.path.dirname(self.video_path))
        base_name, ext = os.path.splitext(os.path.basename(self.video_path))

        for i, (start_ms, end_ms) in enumerate(self.segments):
            start_str = self.ms_to_time_str(start_ms)
            end_str = self.ms_to_time_str(end_ms)
            output_file = os.path.join(output_path, f"{base_name}_cut_{i+1}{ext}")
            
            command = f'ffmpeg -i "{self.video_path}" -ss {start_str} -to {end_str} -c copy "{output_file}"'
            
            self.parent.batch_processor.add_to_queue_and_run(command, output_file)
        
        QMessageBox.information(self, "Processing Started", f"{len(self.segments)} cut operations have been added to the queue.")
        self.accept()
