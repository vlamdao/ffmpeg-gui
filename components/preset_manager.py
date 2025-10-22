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
        self.setup_preset_table()
        self.load_presets()

    def setup_preset_table(self):
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
        
        # Connect signals
        self.preset_table.cellDoubleClicked.connect(self.parent.apply_preset_command)
        self.preset_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preset_table.customContextMenuRequested.connect(self.parent.preset_context_menu)
    
    def load_presets(self):
        presets = []
        if os.path.exists("presets.json"):
            with open("presets.json", "r", encoding="utf-8") as f:
                presets = json.load(f)
        self.load_presets_into_table(presets)

    def load_presets_into_table(self, presets):
        """Populate the preset table with data"""
        self.preset_table.setRowCount(0)
        for preset in presets:
            row = self.preset_table.rowCount()
            self.preset_table.insertRow(row)
            name_item = QTableWidgetItem(preset['name'])
            cmd_item = QTableWidgetItem(preset['command'])
            self.preset_table.setItem(row, 0, name_item)
            self.preset_table.setItem(row, 1, cmd_item)

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
            cmd_item = self.preset_table.item(row, 1)
            if cmd_item:
                self.cmd_input.setPlainText(cmd_item.text())

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
    def __init__(self, parent=None, title="Preset", preset_name="", preset_command=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setup_ui(preset_name, preset_command)

    def setup_ui(self, preset_name, preset_command):
        layout = QVBoxLayout(self)

        # Name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Preset name:")
        name_label.setFixedWidth(80)
        self.name_input = QLineEdit(preset_name)
        self.name_input.setFixedWidth(500)

        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Command input
        cmd_layout = QHBoxLayout()
        cmd_label = QLabel("Command:")
        cmd_label.setFixedWidth(80)
        self.cmd_input = QTextEdit(preset_command)
        self.cmd_input.setFixedHeight(70)
        self.cmd_input.setFixedWidth(500)
        self.cmd_input.setFont(QFont("Consolas", 9))
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.cmd_input)
        layout.addLayout(cmd_layout)

        # Buttons
        button_style = """
            QPushButton {
                font-size: 13px;
                padding: 10px 20px;
                font-weight: semi-bold;
            }
        """
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        ok_button = QPushButton("OK")
        ok_button.setStyleSheet(button_style)
        ok_button.setIcon(QIcon(resource_path("icon/ok.png")))
        ok_button.setIconSize(QSize(24, 24))
        ok_button.setFixedWidth(200)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(button_style)
        cancel_button.setIcon(QIcon(resource_path("icon/cancel.png")))
        cancel_button.setIconSize(QSize(24, 24))
        cancel_button.setFixedWidth(200)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

