from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import (
    QFont, QSyntaxHighlighter, QTextCharFormat, QColor
)

class SearchHighlighter(QSyntaxHighlighter):
    """
    A QSyntaxHighlighter to highlight search results in a QTextEdit.

    This class finds all occurrences of a text pattern case-insensitively
    and highlights them. It also supports highlighting a "current" match
    with a different color.
    """
    def __init__(self, parent=None):
        """Initializes the SearchHighlighter."""
        super().__init__(parent)
        self._pattern = ""
        self._current_match_pos = -1

        # matched result with yellow background 
        self.match_format = QTextCharFormat()
        self.match_format.setBackground(QColor("yellow"))

        # current matched result will have lightgreen background
        self.current_match_format = QTextCharFormat()
        self.current_match_format.setBackground(QColor("lightgreen"))

    def set_pattern(self, pattern: str, current_match_pos: int = -1):
        """
        Sets the search pattern and the position of the current match to highlight.

        Args:
            pattern (str): The text string to search for.
            current_match_pos (int): The starting position of the current match
                                     to be specially highlighted. Defaults to -1 (none).
        """
        # lower new pattern (search text) for easy searching
        new_pattern_lower = pattern.lower()
        if self._pattern != new_pattern_lower:
            self._pattern = new_pattern_lower

        self._current_match_pos = current_match_pos
        self.rehighlight()

    def highlightBlock(self, text: str):
        """
        Highlights a block of text based on the set pattern.

        This function is automatically called by Qt for each text block in the document.
        It searches for the pattern within the block and applies the appropriate
        highlighting format.
        
        Args:
            text (str): The text block to be highlighted.
        """
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
            # Tái sử dụng các đối tượng format đã được tạo sẵn.
            if absolute_pos == self._current_match_pos:
                self.setFormat(index, length, self.current_match_format)
            else:
                self.setFormat(index, length, self.match_format)

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
        self.search_pattern = ""
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
        self.search_pattern = text
        self.current_match = -1
        self.search_next()
        
    def search_previous(self):
        if not self.search_pattern:
            return
        
        text = self.log_view.toPlainText().lower()
        search_pattern = self.search_pattern.lower()
        
        if self.current_match == -1:
            self.current_match = text.count(search_pattern) - 1
        else:
            self.current_match = (self.current_match - 1) % text.count(search_pattern)
            
        self.highlight_current_match()
        
    def search_next(self):
        if not self.search_pattern:
            return
            
        text = self.log_view.toPlainText().lower()
        search_pattern = self.search_pattern.lower()
        
        if text.count(search_pattern) > 0:
            self.current_match = (self.current_match + 1) % text.count(search_pattern)
            self.highlight_current_match()
            
    def get_match_position(self, match_index):
        """Get the position of a specific match in the text"""
        if match_index < 0:
            return -1
            
        text = self.log_view.toPlainText().lower()
        search_pattern = self.search_pattern.lower()
        
        current_pos = 0
        for i in range(match_index + 1):
            current_pos = text.find(search_pattern, current_pos)
            if current_pos == -1:  # if no match found
                return -1
            if i < match_index:
                current_pos += 1
                
        return current_pos

    def highlight_current_match(self):
        position = self.get_match_position(self.current_match)
        self.highlighter.set_pattern(self.search_pattern, position)
        
        if position >= 0:
            # Create a cursor and move it to the match position
            cursor = self.log_view.textCursor()
            cursor.setPosition(position)
            
            # Set the cursor in the text edit
            self.log_view.setTextCursor(cursor)
            
            # Ensure the cursor is visible by scrolling to it
            self.log_view.ensureCursorVisible()