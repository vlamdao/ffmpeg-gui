import json, os
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QFormLayout,
    QMessageBox, QMenu, QDialog, QTextEdit,
    QLineEdit, QHeaderView,  QDialogButtonBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from helper import FontDelegate
from .preset_dialog import PresetDialog

class _PresetStore:
    """Handles the persistence (loading/saving) of presets to a JSON file."""
    _PRESET_FILE = "presets.json"

    def load(self) -> list[dict]:
        """Loads presets from the JSON file. Returns an empty list if not found."""
        if not os.path.exists(self._PRESET_FILE):
            return []
        try:
            with open(self._PRESET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading presets: {e}")
            return []

    def save(self, presets: list[dict]):
        """Saves the list of presets to the JSON file."""
        with open(self._PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)

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
        self._parent = parent
        self._preset_table = preset_table
        self._cmd_input = cmd_input
        self._store = _PresetStore()
        self._presets = []
        
        # Setup preset table
        self._setup_preset_table()
        self._load_presets()

    def _setup_preset_table(self):
        """Configures the appearance and behavior of the preset table widget."""
        self._preset_table.setColumnCount(2)
        self._preset_table.setHorizontalHeaderLabels(['Preset Name', 'Command Template'])
        # stretch the last column to fill available space
        self._preset_table.horizontalHeader().setStretchLastSection(True)
        # disable editing when double-clicked on item
        self._preset_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # select entire row when clicked on an item
        self._preset_table.setSelectionBehavior(QTableWidget.SelectRows)
        # set minimum height for the preset table
        self._preset_table.setMinimumHeight(100)
        # set monospace font for command template column
        self._preset_table.setItemDelegateForColumn(1, FontDelegate(font_family="Consolas", font_size=9))
        # set preset name column width to 300 pixels
        self._preset_table.setColumnWidth(0, 300)
        
        preset_table_header = self._preset_table.horizontalHeader()
        # allow resizing of preset name column
        preset_table_header.setSectionResizeMode(0, QHeaderView.Interactive)
        # disable auto bold for header sections when select a item
        preset_table_header.setHighlightSections(False)
        # stretch command template column to fill available space
        preset_table_header.setSectionResizeMode(1, QHeaderView.Stretch)
        vertical_header = self._preset_table.verticalHeader()
        vertical_header.setHighlightSections(False)
        # set minimum height to show 5 rows
        rows_to_show = 2
        row_height = self._preset_table.verticalHeader().defaultSectionSize()
        header_height = self._preset_table.horizontalHeader().height()
        total_height = row_height * rows_to_show + header_height + 1
        self._preset_table.setMinimumHeight(total_height)
        self._preset_table.setContextMenuPolicy(Qt.CustomContextMenu)
    
    def _load_presets(self):
        """Loads presets from 'presets.json' and populates the table.

        If the file doesn't exist, it proceeds with an empty list.
        """
        self._presets = self._store.load()
        self._populate_table_from_model()

    def _populate_table_from_model(self):
        """Populate the table with preset data.
        Args:
            presets (list[dict]): A list of dictionaries, where each
                                 dictionary represents a preset and contains
                                 'name' and 'command' keys.
        """
        self._preset_table.setRowCount(0)
        for preset in self._presets:
            row = self._preset_table.rowCount()
            self._preset_table.insertRow(row)
            preset_name_item = QTableWidgetItem(preset['name'])
            command_template_item = QTableWidgetItem(preset['command'])
            self._preset_table.setItem(row, 0, preset_name_item)
            self._preset_table.setItem(row, 1, command_template_item)

    def add_preset(self):
        """Opens a dialog to add a new preset.

        After the user enters a name and command, it validates the input,
        checks for duplicate names, and adds the new preset to the table
        and saves it to the file.
        """
        dialog = PresetDialog(self._parent, "Add Preset")
        if dialog.exec_() == QDialog.Accepted:
            preset_name, command = dialog.get_preset()
            
            if not preset_name or not command:
                QMessageBox.warning(self._parent, "Error", "Both fields are required!")
                return

            # Check for duplicate preset names
            if any(p['name'] == preset_name for p in self._presets):
                QMessageBox.warning(self._parent, "Error", "Preset name already exists!")
                return

            # Add to model, save, and refresh view
            self._presets.append({'name': preset_name, 'command': command})
            self._store.save(self._presets)
            self._populate_table_from_model()

    def edit_preset(self, row: int):
        """Opens a dialog to edit an existing preset at a given row.

        Args:
            row (int): The table row of the preset to be edited.
        """
        if row < 0:
            return

        preset_to_edit = self._presets[row]
        old_name = preset_to_edit['name']
        old_command = preset_to_edit['command']

        dialog = PresetDialog(self._parent, "Edit Preset", old_name, old_command)
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_command = dialog.get_preset()

            if not new_name or not new_command:
                QMessageBox.warning(self._parent, "Error", "Both fields are required!")
                return

            # Check for duplicate names (except current preset)
            if any(p['name'] == new_name for i, p in enumerate(self._presets) if i != row):
                QMessageBox.warning(self._parent, "Error", "Preset name already exists!")
                return

            self._presets[row] = {'name': new_name, 'command': new_command}
            self._store.save(self._presets)
            self._populate_table_from_model()

    def delete_preset(self, row: int):
        """Deletes the preset at the specified row after user confirmation.

        Args:
            row (int): The table row of the preset to be deleted.
        """
        if row < 0:
            return

        preset_name = self._presets[row]['name']
        reply = QMessageBox.question(
            self._parent,
            "Confirm Delete",
            f"Are you sure you want to delete preset '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self._presets[row]
            self._store.save(self._presets)
            self._populate_table_from_model()

    def apply_preset(self, row: int, col: int):
        """Applies the selected preset's command to the main command input field.

        This is typically connected to the `cellDoubleClicked` signal.

        Args:
            row (int): The row of the cell that was double-clicked.
            col (int): The column of the cell that was double-clicked (unused).
        """
        if row >= 0:
            command_template = self._presets[row]['command']
            self._cmd_input.setPlainText(command_template)

    def show_context_menu(self, pos):
        """Shows a context menu (Edit, Delete) for the preset table."""
        row = self._preset_table.rowAt(pos.y())
        # Do not show menu if right-clicking on the header or empty space
        if row < 0:
            return

        menu = QMenu(self._parent)
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(self._preset_table.viewport().mapToGlobal(pos))
        
        if action == edit_action:
            self.edit_preset(row)
        elif action == delete_action:
            self.delete_preset(row)
