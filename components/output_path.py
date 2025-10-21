from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
import os 

class OutputPath(QWidget):
    def __init__(self, parent=None, default_path="./output"):
        super().__init__(parent)
        self.parent = parent
        self.default_path = default_path
        self.setup_ui()

    def setup_ui(self):
        """Setup the output path interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.out_label = QLabel("Output path:")
        self.out_label.setFixedWidth(80)
        layout.addWidget(self.out_label)

        # Path input
        self.out_input = QLineEdit(self.default_path)
        layout.addWidget(self.out_input)

        # Browse button
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_output)
        layout.addWidget(self.browse_btn)

    def browse_output(self):
        """Open dialog to choose output directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.get_path()  # Start from current path
        )
        if path:
            self.set_path(path)

    # Getter and Setter methods
    def get_path(self):
        """Get the current output path"""
        return self.out_input.text().strip()

    def set_path(self, path):
        """Set the output path"""
        self.out_input.setText(path)

    def create_output_directory(self):
        """Create output directory if it doesn't exist"""
        import os
        path = self.get_path()
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                return True
            except OSError:
                return False
        return True

    def get_completed_output_path(self, inputfile_folder, filename=None):
        path = self.get_path()
        if path in ('./', '.'):
            out_dir = inputfile_folder
        elif path.startswith('./'):
            out_dir = os.path.join(inputfile_folder, path.strip('./'))
        else:
            out_dir = path
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
     
        if filename:
            return os.path.join(out_dir, filename)
        return out_dir