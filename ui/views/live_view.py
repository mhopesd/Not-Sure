import customtkinter as ctk
from ui.styles import *

class LiveMeetingView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=C_BG_DARK, corner_radius=0)
        self.grid(row=0, column=0, sticky="nsew")
        self.timer_seconds = 0
        self.timer_running = False
        
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)
        
        self.timer_label = ctk.CTkLabel(self.center_frame, text="00:00", font=("Arial", 64, "bold"), text_color="white")
        self.timer_label.pack(pady=20)
        
        self.status_ind = ctk.CTkLabel(self.center_frame, text="● Listening...", font=("Arial", 16), text_color=C_PURPLE)
        self.status_ind.pack(pady=(0, 20))

        # VU Meter
        self.vu_meter = ctk.CTkProgressBar(self.center_frame, height=10, width=400, progress_color=C_PURPLE)
        self.vu_meter.pack(pady=(0, 40))
        self.vu_meter.set(0)
        
        ctk.CTkLabel(self.center_frame, text="Live Transcript", font=("Arial", 14, "bold"), text_color="gray60", anchor="w").pack(fill="x", pady=(0, 10))
        self.transcript_box = ctk.CTkTextbox(self.center_frame, font=("Consolas", 16), text_color="#E0E0E0", fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.transcript_box.pack(fill="both", expand=True)
        self.transcript_box.configure(state="disabled") # Set read-only by default

    def update_transcript(self, text):
        self.transcript_box.configure(state="normal") # Enable for update
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.insert("1.0", text)
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled") # Disable again

    def update_level(self, level):
        # Update progress bar
        # Add slight gain/smoothing if needed, but direct mapping is fine
        self.vu_meter.set(level * 5) # Boost visually since speech is often low RMS

    def reset(self):
        self.timer_seconds = 0
        self.vu_meter.set(0)
        self.timer_label.configure(text="00:00")
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")

    def start_timer(self):
        if self.timer_running: return # Prevent duplicate loops
        self.timer_running = True
        self._tick()

    def stop_timer(self):
        self.timer_running = False

    def _tick(self):
        if self.timer_running:
            self.timer_seconds += 1
            m, s = divmod(self.timer_seconds, 60)
            self.timer_label.configure(text=f"{m:02d}:{s:02d}")
            self.after(1000, self._tick)
