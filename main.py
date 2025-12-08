# main.py
from src.gui_app import WarframeMonitorGUI
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    # app = WarframeMonitorGUI(root, debug=True)
    app = WarframeMonitorGUI(root, debug=False)
    root.mainloop()