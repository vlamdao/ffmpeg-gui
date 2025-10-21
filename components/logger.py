from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import (QFont, QSyntaxHighlighter, QTextCharFormat, QColor)

class SearchHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pattern = ""
        self.current_pos = -1
        self. match_color = QColor("yellow")
        self.current_color = QColor("lightgreen")

    def setPattern(self, pattern, current_pos=-1):
        self._pattern = pattern.lower()
        self.current_pos = current_pos
        self.rehighlight()

    def highlightBlock(self, text):
        if not self._pattern:
            return
        text_lower = text.lower()
        start = 0
        block_pos = self.currentBlock().position()
        length = len(self._pattern)
        while True:
            index = text_lower.find(self._pattern, start)
            if index == -1:
                break
            absolute_pos = block_pos + index
            fmt = QTextCharFormat()
            if absolute_pos == self.current_pos:
                fmt.setBackground(self.current_color)
            else:
                fmt.setBackground(self.match_color)
            self.setFormat(index, length, fmt)
            start = index + length

class Logger(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Log text area
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("FFmpeg output will appear here...")
        self.log_view.setFont(QFont("Consolas", 8))
        self.log_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.log_view)
        
        # Search layout
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search log...")
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.search_previous)
        self.prev_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.search_next)
        self.next_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.prev_btn)
        search_layout.addWidget(self.next_btn)
        layout.addLayout(search_layout)

        # =======================================
        # Setup highlighter
        # =======================================
        self.highlighter = SearchHighlighter(self.log_view.document())
        self.search_input_text = ""
        self.current_match = -1

    def get_widget(self):
        return self

    def append_log(self, msg):
        self.log_view.append(msg)
        
    def clear(self):
        self.log_view.clear()
        
    def perform_search(self, text=None):
        if text is None:
            text = self.search_input.text()
        self.search_input_text = text
        self.current_match = -1
        self.search_next()
        
    def search_previous(self):
        if not self.search_input_text:
            return
        
        text = self.log_view.toPlainText().lower()
        search_text = self.search_input_text.lower()
        
        if self.current_match == -1:
            self.current_match = text.count(search_text) - 1
        else:
            self.current_match = (self.current_match - 1) % text.count(search_text)
            
        self.highlight_current_match()
        
    def search_next(self):
        if not self.search_input_text:
            return
            
        text = self.log_view.toPlainText().lower()
        search_text = self.search_input_text.lower()
        
        if text.count(search_text) > 0:
            self.current_match = (self.current_match + 1) % text.count(search_text)
            self.highlight_current_match()
            
    def get_match_position(self, match_index):
        """Get the position of a specific match in the text"""
        if match_index < 0:
            return -1
            
        text = self.log_view.toPlainText().lower()
        search_text = self.search_input_text.lower()
        
        current_pos = 0
        for i in range(match_index + 1):
            current_pos = text.find(search_text, current_pos)
            if current_pos == -1:  # if no match found
                return -1
            if i < match_index:
                current_pos += 1
                
        return current_pos

    def highlight_current_match(self):
        position = self.get_match_position(self.current_match)
        self.highlighter.setPattern(self.search_input_text, position)
        
        if position >= 0:
            # Create a cursor and move it to the match position
            cursor = self.log_view.textCursor()
            cursor.setPosition(position)
            
            # Set the cursor in the text edit
            self.log_view.setTextCursor(cursor)
            
            # Ensure the cursor is visible by scrolling to it
            self.log_view.ensureCursorVisible()