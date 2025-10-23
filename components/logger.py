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

    # Inherited from QSyntaxHighlighter
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
            # Reuse pre-created format objects.
            if absolute_pos == self._current_match_pos:
                self.setFormat(index, length, self.current_match_format)
            else:
                self.setFormat(index, length, self.match_format)

            start = index + length

class Logger(QWidget):
    """
    A widget for displaying logs with search and highlighting capabilities.

    This component consists of a read-only text area for log messages and
    a search bar with "Previous" and "Next" buttons to navigate through
    search results.
    """
    def __init__(self):
        """Initializes the Logger widget."""
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Sets up the user interface for the logger and search controls."""
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
        self.search_input.returnPressed.connect(self._on_search_enter_pressed)
        self.search_input.textChanged.connect(self._on_search_text_changed)
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
        self.current_match_index = -1
        self._search_results = []
        self._search_results_dirty = True

    def _on_search_enter_pressed(self):
        """Handles the Enter key press in the search input field."""
        current_text = self.search_input.text()
        # If the search text is new, perform a new search.
        # Otherwise, just find the next occurrence.
        if current_text != self.search_pattern:
            self.perform_search(current_text)
        else:
            self.search_next()

    def _on_search_text_changed(self, text: str):
        """Clears highlighting if the search input is empty."""
        if not text:
            self.search_pattern = ""
            self.current_match_index = -1
            self._search_results = []
            self._search_results_dirty = True
            self.highlighter.set_pattern("") # Trigger rehighlight with no pattern

    def _update_search_results_if_needed(self):
        """Performs search and caches results if the pattern or log has changed."""
        if not self.search_pattern:
            self._search_results = []
            self.highlighter.set_pattern("")
            return

        if self._search_results_dirty:
            self._search_results = []
            text = self.log_view.toPlainText()
            # Use QRegularExpression for a more robust and potentially faster search
            # but for now, we stick to the simple find
            pattern_lower = self.search_pattern.lower()
            text_lower = text.lower()
            
            start = 0
            while True:
                index = text_lower.find(pattern_lower, start)
                if index == -1:
                    break
                self._search_results.append(index)
                start = index + 1
            
            self._search_results_dirty = False

    def get_widget(self):
        """Returns the widget instance itself."""
        return self

    def append_log(self, msg):
        """
        Appends a new message to the log view.

        Args:
            msg (str): The message to append.
        """
        self.log_view.append(msg)
        # Invalidate search results when new log is added
        self._search_results_dirty = True
        
    def clear(self):
        """Clears all messages from the log view."""
        self.log_view.clear()
        
    def perform_search(self, text=None):
        """
        Initiates a new search for the given text.

        If no text is provided, it uses the current text from the search input.
        It resets the search state and finds the first match.

        Args:
            text (str, optional): The text to search for. Defaults to None.
        """
        if text is None:
            text = self.search_input.text()
        self.search_pattern = text
        self.current_match_index = -1
        self._search_results_dirty = True
        self.search_next()
        
    def search_previous(self):
        """Finds and highlights the previous occurrence of the search pattern."""
        if not self.search_pattern:
            return
        
        self._update_search_results_if_needed()
        if not self._search_results:
            return

        num_matches = len(self._search_results)
        self.current_match_index = (self.current_match_index - 1 + num_matches) % num_matches
        self.highlight_current_match()
        
    def search_next(self):
        """Finds and highlights the next occurrence of the search pattern."""
        if not self.search_pattern:
            return

        self._update_search_results_if_needed()
        if not self._search_results:
            return

        num_matches = len(self._search_results)
        self.current_match_index = (self.current_match_index + 1) % num_matches
        self.highlight_current_match()

    def highlight_current_match(self):
        """
        Highlights the current search match and scrolls the view to it.

        This method updates the highlighter to mark the current match with a
        special color and ensures it is visible on the screen.
        """
        if not self._search_results or self.current_match_index < 0:
            self.highlighter.set_pattern(self.search_pattern, -1)
            return

        position = self._search_results[self.current_match_index]
        self.highlighter.set_pattern(self.search_pattern, position)
        
        if position >= 0:
            # Create a cursor and move it to the match position
            cursor = self.log_view.textCursor()
            cursor.setPosition(position)
            
            # Set the cursor in the text edit
            self.log_view.setTextCursor(cursor)
            
            # Ensure the cursor is visible by scrolling to it
            self.log_view.ensureCursorVisible()