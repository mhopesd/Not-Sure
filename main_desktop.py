import sys
import os

# Ensure we can import from local directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui_modern import JamieCloneApp

if __name__ == "__main__":
    app = JamieCloneApp()
    app.mainloop()
