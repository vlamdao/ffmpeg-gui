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
