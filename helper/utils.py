import sys
import os
from PyQt5.QtCore import QTime

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def ms_to_time_str(ms):
    time = QTime(0, 0, 0).addMSecs(ms)
    return time.toString("HH:mm:ss.zzz")

def time_str_to_ms(time_str: str) -> int:
    """Converts a time string 'HH:mm:ss.zzz' to milliseconds."""
    # Qt's fromString is flexible and can handle formats with or without milliseconds
    time = QTime.fromString(time_str, "HH:mm:ss.zzz")
    if not time.isValid():
        # Try parsing without milliseconds if the first attempt fails
        time = QTime.fromString(time_str, "HH:mm:ss")
        if not time.isValid():
            raise ValueError(f"Invalid time string format: {time_str}")
    return QTime(0, 0, 0).msecsTo(time)

def bold_green(text: str):
    return f'<span style="color:green; font-weight:bold;">{text}</span>'

def bold_red(text: str):
    return f'<span style="color:red; font-weight:bold;">{text}</span>'

def bold_yellow(text: str):
    return f'<span style="color:yellow; font-weight:bold;">{text}</span>'

def bold_blue(text: str):
    return f'<span style="color:blue; font-weight:bold;">{text}</span>'

def styled_text(color: str, font_weight: str, font_style: str, text: str):
    return f'<span style="color:{color}; font-weight:{font_weight}; font-style:{font_style};">{text}</span>'


