from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog
)
from pathlib import Path

class OutputPath(QWidget):
    """A widget for selecting and managing the output directory."""
    def __init__(self, parent: QWidget | None = None, default_path: str = "./output"):
        """Initializes the OutputPath widget.

        Args:
            parent (QWidget | None, optional): The parent widget. Defaults to None.
            default_path (str, optional): The default path to display. Defaults to "./output".
        """
        super().__init__(parent)
        self.parent = parent
        self._default_path = str(Path(default_path)) # Normalize path
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the user interface, including the label, text input, and browse button."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._path_label = QLabel("Output folder")
        self._path_label.setFixedWidth(85)
        layout.addWidget(self._path_label)

        # Path input
        self._path_input = QLineEdit(self._default_path)
        layout.addWidget(self._path_input)

        # Browse button
        self._browse_button = QPushButton("Browse...")
        self._browse_button.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self._browse_button)

    def _on_browse_clicked(self):
        """Opens a dialog to choose an output directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.get_path() # Start browsing from the current path
        )
        if path:
            self.set_path(path)

    def get_path(self) -> str:
        """Gets the current output path from the input field."""
        return self._path_input.text().strip()

    def set_path(self, path: str):
        """Sets the output path in the input field."""
        self._path_input.setText(path)

    def get_completed_output_path(self, input_file_folder: str, filename: str | None = None) -> str:
        """
        Resolves the final output path based on user input and the input file's location.

        - If the path is absolute, it's used directly.
        - If the path is relative (e.g., '.', './output'), it's resolved relative
          to the input file's folder.

        The directory is created if it doesn't exist.

        Args:
            input_file_folder (str): The folder path of the source file.
            filename (str | None): An optional filename to append to the path.

        Returns:
            str: The absolute, resolved output path.
        """
        user_path_str = self.get_path()
        user_path = Path(user_path_str)
        input_folder_path = Path(input_file_folder)

        if user_path.is_absolute():
            output_dir = user_path
        else:
            # Resolve relative path against the input file's folder
            output_dir = input_folder_path.joinpath(user_path).resolve()

        output_dir.mkdir(parents=True, exist_ok=True)

        if filename:
            return str(output_dir / filename)
        return str(output_dir)