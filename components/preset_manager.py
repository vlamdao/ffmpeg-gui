import json, os
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QInputDialog, 
    QMessageBox, QMenu, QDialog, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QHeaderView, QTextEdit
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize
from utils import resource_path
from .delegate import FontDelegate

class PresetManager:
    def __init__(self, parent, preset_table, cmd_input):
        self.parent = parent
        self.preset_table = preset_table
        self.cmd_input = cmd_input
        
        # Setup preset table
        self._setup_preset_table()
        self._load_presets()

    def _setup_preset_table(self):
        """Setup the preset table with all necessary configurations"""
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
        self.preset_table.setItemDelegateForColumn(1, FontDelegate(font_family="Consolas"))
        # set preset name column width to 300 pixels
        self.preset_table.setColumnWidth(0, 300)
        
        preset_table_header = self.preset_table.horizontalHeader()
        # allow resizing of preset name column
        preset_table_header.setSectionResizeMode(0, QHeaderView.Interactive)
        # disable auto bold for header sections when select a item
        preset_table_header.setHighlightSections(False)
        # stretch command template column to fill available space
        preset_table_header.setSectionResizeMode(1, QHeaderView.Stretch)

        # set minimum height to show 5 rows
        rows_to_show = 2
        row_height = self.preset_table.verticalHeader().defaultSectionSize()
        header_height = self.preset_table.horizontalHeader().height()
        total_height = row_height * rows_to_show + header_height + 1
        self.preset_table.setMinimumHeight(total_height)
        self.preset_table.setContextMenuPolicy(Qt.CustomContextMenu)
    
    def _load_presets(self):
        presets = []
        if os.path.exists("presets.json"):
            with open("presets.json", "r", encoding="utf-8") as f:
                presets = json.load(f)
        self._load_presets_into_table(presets)

    def _load_presets_into_table(self, presets):
        """Populate the preset table with data"""
        self.preset_table.setRowCount(0)
        for preset in presets:
            row = self.preset_table.rowCount()
            self.preset_table.insertRow(row)
            preset_name_item = QTableWidgetItem(preset['name'])
            command_template_item = QTableWidgetItem(preset['command'])
            self.preset_table.setItem(row, 0, preset_name_item)
            self.preset_table.setItem(row, 1, command_template_item)

    def add_preset(self):
        """Show dialog to add new preset"""
        dialog = PresetDialog(self.parent, "Add Preset")
        if dialog.exec_() == QDialog.Accepted:
            preset_name = dialog.name_input.text().strip()
            command = dialog.cmd_input.toPlainText().strip()
            
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

    def edit_preset(self, row):
        """Edit existing preset"""
        if row < 0:
            return

        old_name = self.preset_table.item(row, 0).text()
        old_command = self.preset_table.item(row, 1).text()

        dialog = PresetDialog(self.parent, "Edit Preset", old_name, old_command)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.name_input.text().strip()
            new_command = dialog.cmd_input.toPlainText().strip()

            if not new_name or not new_command:  # was checking undefined 'command' variable
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

    def delete_preset(self, row):
        """Delete preset at specified row"""
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

    def apply_preset(self, row):
        """Apply preset command to main command input"""
        if row >= 0:
            command_template_item = self.preset_table.item(row, 1)
            if command_template_item:
                self.cmd_input.setPlainText(command_template_item.text())

    def show_context_menu(self, pos):
        """Show context menu for preset table"""
        row = self.preset_table.rowAt(pos.y())
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
        """Save presets to file"""
        presets = []
        for row in range(self.preset_table.rowCount()):
            presets.append({
                'name': self.preset_table.item(row, 0).text(),
                'command': self.preset_table.item(row, 1).text()
            })
        with open("presets.json", "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)

class PresetDialog(QDialog):
    _LABEL_WIDTH = 80
    _INPUT_WIDTH = 500
    _CMD_INPUT_HEIGHT = 70
    _BUTTON_WIDTH = 200
    _ICON_SIZE = QSize(24, 24)
    _BUTTON_STYLE = """
        QPushButton {
            font-size: 13px;
            padding: 10px 20px;
            font-weight: semi-bold;
        }
    """

    def __init__(self, parent=None, title="Preset", preset_name="", preset_command=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._preset_name = preset_name
        self._preset_command = preset_command

        self._setup_ui()

    def _setup_ui(self):
        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.name_label = QLabel("Preset name:")
        self.name_label.setFixedWidth(self._LABEL_WIDTH)
        self.name_input = QLineEdit(self._preset_name)
        self.name_input.setFixedWidth(self._INPUT_WIDTH)

        self.cmd_label = QLabel("Command:")
        self.cmd_label.setFixedWidth(self._LABEL_WIDTH)
        self.cmd_input = QTextEdit(self._preset_command)
        self.cmd_input.setFixedHeight(self._CMD_INPUT_HEIGHT)
        self.cmd_input.setFixedWidth(self._INPUT_WIDTH)
        self.cmd_input.setFont(QFont("Consolas", 9))

        self.ok_button = self._create_button("OK", "icon/ok.png", self.accept)
        self.cancel_button = self._create_button("Cancel", "icon/cancel.png", self.reject)

    def _create_layout(self):
        main_layout = QVBoxLayout(self)

        name_layout = QHBoxLayout()
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        cmd_layout = QHBoxLayout()
        cmd_layout.addWidget(self.cmd_label)
        cmd_layout.addWidget(self.cmd_input)
        main_layout.addLayout(cmd_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

    def _create_button(self, text, icon_path, on_click):
        button = QPushButton(text)
        button.setStyleSheet(self._BUTTON_STYLE)
        button.setIcon(QIcon(resource_path(icon_path)))
        button.setIconSize(self._ICON_SIZE)
        button.setFixedWidth(self._BUTTON_WIDTH)
        button.clicked.connect(on_click)
        return button
