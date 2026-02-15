import sys
import os
import logging
import threading
import time

# Ensure we can import from local directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui_modern import JamieCloneApp
from chaos_engineering import ChaosMonkey, ErrorMonitor

# Configure main app logging to stdout as well
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("WARNING: STARTING IN CHAOS MODE")
    
    # 1. Initialize Agents
    monitor = ErrorMonitor()
    chaos = ChaosMonkey(monitor, probability=0.4) # 40% chance of failure
    
    # 2. Initialize App
    app = JamieCloneApp()
    
    # 3. Inject Chaos (Wait for audio_app to be ready)
    def inject_when_ready():
        print("Waiting for audio backend to initialize...")
        while not hasattr(app, "audio_app") or app.audio_app is None:
            time.sleep(0.5)
        
        print("Backend ready. Injecting Chaos...")
        chaos.apply_patches(app.audio_app)
        app.update_loading_status("WARNING: CHAOS AGENT ACTIVE")

    threading.Thread(target=inject_when_ready, daemon=True).start()

    # 4. Run App
    try:
        app.mainloop()
    except Exception as e:
        monitor.log_failure("MainLoop", type(e).__name__, str(e), "See log for stack.")
