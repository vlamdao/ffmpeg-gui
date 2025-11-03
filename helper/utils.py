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


def styled_text(font_weight: str | None, 
                color: str | None,
                font_style: str | None, 
                text: str):
    if not font_weight:
        font_weight = 'normal'
    if not color:
        color = 'black'
    if not font_style:
        font_style = 'normal'
    if color == 'yellow':
        color = 'goldenrod'
    return f'<span style="font-weight:{font_weight}; color:{color}; font-style:{font_style};">{text}</span>'
    
def folder_name_ext_from_path(path: str):
    folder = os.path.dirname(path)
    filename = os.path.basename(path)
    name, ext = os.path.splitext(filename)
    ext = ext.lstrip('.')
    return folder, name, ext