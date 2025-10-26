import json, os
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QFormLayout,
    QMessageBox, QMenu, QDialog, QTextEdit,
    QLineEdit, QHeaderView,  QDialogButtonBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from helper import FontDelegate

class PresetManager:
    """Manages the creation, loading, editing, and saving of FFmpeg command presets.

    This class controls the preset table UI, handles user interactions like
    adding, editing, deleting, and applying presets, and manages the persistence
    of presets to a JSON file.
    """
    def __init__(self, parent, preset_table, cmd_input):
        """Initializes the PresetManager.

        Args:
            parent (QWidget): The parent widget, typically the main application window.
            preset_table (QTableWidget): The table widget used to display presets.
            cmd_input (QTextEdit): The command input widget where presets will be applied.
        """
        self.parent = parent
        self.preset_table = preset_table
        self.cmd_input = cmd_input
        
        # Setup preset table
        self._setup_preset_table()
        self._load_presets()

    def _setup_preset_table(self):
        """Configures the appearance and behavior of the preset table widget."""
        self.preset_table.setColumnCount(2)
        self.preset_table.setHorizontalHeaderLabels(['Preset Name', 'Command Template'])
        # stretch the last column to fill available space
        self.preset_table.horizontalHeader().setStretchLastSection(True)
        # disable editing when double-clicked on item
        self.preset_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # select entire row when clicked on an item
        self.preset_table.setSelectionBehavior(QTableWidget.SelectRows)
        # set minimum height for the preset table
        self.preset_table.setMinimumHeight(100)
        # set monospace font for command template column
        self.preset_table.setItemDelegateForColumn(1, FontDelegate(font_family="Consolas", font_size=9))
        # set preset name column width to 300 pixels
        self.preset_table.setColumnWidth(0, 300)
        
        preset_table_header = self.preset_table.horizontalHeader()
        # allow resizing of preset name column
        preset_table_header.setSectionResizeMode(0, QHeaderView.Interactive)
        # disable auto bold for header sections when select a item
        preset_table_header.setHighlightSections(False)
        # stretch command template column to fill available space
        preset_table_header.setSectionResizeMode(1, QHeaderView.Stretch)

        vertical_header = self.preset_table.verticalHeader()
        vertical_header.setHighlightSections(False)

        # set minimum height to show 5 rows
        rows_to_show = 2
        row_height = self.preset_table.verticalHeader().defaultSectionSize()
        header_height = self.preset_table.horizontalHeader().height()
        total_height = row_height * rows_to_show + header_height + 1
        self.preset_table.setMinimumHeight(total_height)
        self.preset_table.setContextMenuPolicy(Qt.CustomContextMenu)
    
    def _load_presets(self):
        """Loads presets from 'presets.json' and populates the table.

        If the file doesn't exist, it proceeds with an empty list.
        """
        presets = []
        if os.path.exists("presets.json"):
            with open("presets.json", "r", encoding="utf-8") as f:
                presets = json.load(f)
        self._load_presets_into_table(presets)

    def _load_presets_into_table(self, presets: list[dict]):
        """Populate the table with preset data.
        Args:
            presets (list[dict]): A list of dictionaries, where each
                                 dictionary represents a preset and contains
                                 'name' and 'command' keys.
        """
        self.preset_table.setRowCount(0)
        for preset in presets:
            row = self.preset_table.rowCount()
            self.preset_table.insertRow(row)
            preset_name_item = QTableWidgetItem(preset['name'])
            command_template_item = QTableWidgetItem(preset['command'])
            self.preset_table.setItem(row, 0, preset_name_item)
            self.preset_table.setItem(row, 1, command_template_item)

    def add_preset(self):
        """Opens a dialog to add a new preset.

        After the user enters a name and command, it validates the input,
        checks for duplicate names, and adds the new preset to the table
        and saves it to the file.
        """
        dialog = PresetDialog(self.parent, "Add Preset")
        if dialog.exec_() == QDialog.Accepted:
            preset_name, command = dialog.get_preset()
            
            if not preset_name or not command:
                QMessageBox.warning(self.parent, "Error", "Both fields are required!")
                return

            # Check for duplicate preset names
            for row in range(self.preset_table.rowCount()):
                if self.preset_table.item(row, 0).text() == preset_name:
                    QMessageBox.warning(self.parent, "Error", "Preset name already exists!")
                    return

            # Add new preset to table
            row = self.preset_table.rowCount()
            self.preset_table.insertRow(row)
            self.preset_table.setItem(row, 0, QTableWidgetItem(preset_name))
            self.preset_table.setItem(row, 1, QTableWidgetItem(command))
            self.save_presets()

    def edit_preset(self, row: int):
        """Opens a dialog to edit an existing preset at a given row.

        Args:
            row (int): The table row of the preset to be edited.
        """
        if row < 0:
            return

        old_name = self.preset_table.item(row, 0).text()
        old_command = self.preset_table.item(row, 1).text()

        dialog = PresetDialog(self.parent, "Edit Preset", old_name, old_command)
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_command = dialog.get_preset()

            if not new_name or not new_command:
                QMessageBox.warning(self.parent, "Error", "Both fields are required!")
                return

            # Check for duplicate names (except current preset)
            for i in range(self.preset_table.rowCount()):
                if i != row and self.preset_table.item(i, 0).text() == new_name:
                    QMessageBox.warning(self.parent, "Error", "Preset name already exists!")
                    return

            self.preset_table.setItem(row, 0, QTableWidgetItem(new_name))
            self.preset_table.setItem(row, 1, QTableWidgetItem(new_command))
            self.save_presets()

    def delete_preset(self, row: int):
        """Deletes the preset at the specified row after user confirmation.

        Args:
            row (int): The table row of the preset to be deleted.
        """
        if row < 0:
            return

        preset_name = self.preset_table.item(row, 0).text()
        reply = QMessageBox.question(
            self.parent,
            "Confirm Delete",
            f"Are you sure you want to delete preset '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.preset_table.removeRow(row)
            self.save_presets()

    def apply_preset(self, row: int, col: int):
        """Applies the selected preset's command to the main command input field.

        This is typically connected to the `cellDoubleClicked` signal.

        Args:
            row (int): The row of the cell that was double-clicked.
            col (int): The column of the cell that was double-clicked (unused).
        """
        if row >= 0:
            command_template_item = self.preset_table.item(row, 1)
            if command_template_item:
                self.cmd_input.setPlainText(command_template_item.text())

    def show_context_menu(self, pos):
        """Shows a context menu (Edit, Delete) for the preset table."""
        row = self.preset_table.rowAt(pos.y())
        # Do not show menu if right-clicking on the header or empty space
        if row < 0:
            return

        menu = QMenu(self.parent)
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(self.preset_table.viewport().mapToGlobal(pos))
        
        if action == edit_action:
            self.edit_preset(row)
        elif action == delete_action:
            self.delete_preset(row)

    def save_presets(self):
        """Saves all presets from the table to 'presets.json'."""
        presets = []
        for row in range(self.preset_table.rowCount()):
            presets.append({
                'name': self.preset_table.item(row, 0).text(),
                'command': self.preset_table.item(row, 1).text()
            })
        with open("presets.json", "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)


class PresetDialog(QDialog):
    """A dialog for adding or editing a preset (name and command)."""
    _INPUT_WIDTH = 500
    _CMD_INPUT_HEIGHT = 70

    def __init__(self, parent=None, title="Preset", preset_name="", preset_command=""):
        """Initializes the PresetDialog.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            title (str, optional): The window title for the dialog. Defaults to "Preset".
            preset_name (str, optional): The initial text for the preset name field. Defaults to "".
            preset_command (str, optional): The initial text for the command field. Defaults to "".
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # =======================================
        # Create widgets
        # =======================================
        self.name_input = QLineEdit(preset_name)
        self.cmd_input = QTextEdit(preset_command)
        self.cmd_input.setFont(QFont("Consolas", 9))
        
        # Set initial sizes (can be adjusted by user)
        self.name_input.setMinimumWidth(self._INPUT_WIDTH)
        self.cmd_input.setMinimumWidth(self._INPUT_WIDTH)
        self.cmd_input.setMinimumHeight(self._CMD_INPUT_HEIGHT)

        # =======================================
        # Create layout and add widgets
        # =======================================
        layout = QFormLayout(self)
        layout.addRow("Preset Name:", self.name_input)
        layout.addRow("Command:", self.cmd_input)

        # =======================================
        # Add standard buttons
        # =======================================
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_preset(self):
        """Returns the preset name and command from the input fields."""
        return self.name_input.text().strip(), self.cmd_input.toPlainText().strip()
