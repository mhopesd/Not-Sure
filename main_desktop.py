import sys
import os

# Ensure we can import from local directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        from gui_modern import PersonalAssistantApp
        app = PersonalAssistantApp()
        app.mainloop()
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: source venv/bin/activate && pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        # Try to show a GUI error dialog; fall back to stderr
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", f"Failed to start Personal Assistant:\n\n{e}")
            root.destroy()
        except Exception:
            print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
