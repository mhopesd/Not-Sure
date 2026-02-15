import customtkinter as ctk
from ui.styles import *

class MeetingsView(ctk.CTkFrame):
    def __init__(self, parent, open_callback, history):
        super().__init__(parent, fg_color=C_BG_DARK, corner_radius=0)
        self.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self, text="All Meetings", font=("Arial", 24, "bold"), text_color="white").pack(pady=30, padx=30, anchor="w")
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20)
        
        if not history:
             ctk.CTkLabel(scroll, text="No recordings yet.", text_color="gray50").pack(pady=20)
        else:
            for item in history:
                self.create_row(scroll, item, open_callback)

    def create_row(self, parent, item, callback):
        f = ctk.CTkFrame(parent, fg_color=C_CARD_BG, corner_radius=5)
        f.pack(fill="x", pady=2)
        
        title = item.get("title", "Untitled")
        date = item.get("date", "")
        
        btn = ctk.CTkButton(f, text=f"{date}  -  {title}", fg_color="transparent", anchor="w", text_color="white", hover_color="#2B2B2B", command=lambda: callback(item))
        btn.pack(fill="both", padx=10, pady=10)

class TasksView(ctk.CTkFrame):
    def __init__(self, parent, history):
        super().__init__(parent, fg_color=C_BG_DARK, corner_radius=0)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="Action Items", font=("Arial", 24, "bold"), text_color="white").pack(pady=30, padx=30, anchor="w")
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20)
        
        tasks_found = False
        for entry in history:
            tasks = entry.get("tasks", [])
            if tasks:
                date = entry.get("date", "Unknown Date")
                ctk.CTkLabel(scroll, text=f"From {date}", font=("Arial", 14, "bold"), text_color=C_PURPLE).pack(anchor="w", pady=(10, 5))
                for t in tasks:
                    tasks_found = True
                    desc = t.get('description', str(t))
                    # Simple Checkbox style
                    row = ctk.CTkFrame(scroll, fg_color=C_CARD_BG, corner_radius=5)
                    row.pack(fill="x", pady=2)
                    ctk.CTkCheckBox(row, text=desc, text_color="white", fg_color=C_PURPLE, hover_color=C_PURPLE_HOVER).pack(padx=10, pady=10, anchor="w")
        
        if not tasks_found:
             ctk.CTkLabel(scroll, text="No action items found in history.", text_color="gray50").pack(pady=20)

class PeopleView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=C_BG_DARK, corner_radius=0)
        self.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self, text="People (Coming Soon)", font=("Arial", 24, "bold"), text_color="gray50").pack(expand=True)

class MeetingDetailView(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=C_BG_DARK, corner_radius=0)
        self.grid(row=0, column=0, sticky="nsew")
        
    def load_content(self, data):
        # Clear previous
        for widget in self.winfo_children(): widget.destroy()
        
        # Header
        title = data.get("title", "Untitled")
        date = data.get("date", "")
        duration = data.get("duration", "")
        start = data.get("start_time", "")
        end = data.get("end_time", "")
        
        subtext = date
        if duration: subtext += f"  •  {duration}"
        if start and end: subtext += f"  ({start} - {end})"

        ctk.CTkLabel(self, text=title, font=("Arial", 28, "bold"), text_color="white", wraplength=800, justify="left").pack(pady=(30, 5), padx=40, anchor="w")
        ctk.CTkLabel(self, text=subtext, font=("Arial", 14), text_color="gray60").pack(pady=(0, 20), padx=40, anchor="w")
        
        # Speaker Info
        speaker_info = data.get("speaker_info", {})
        if speaker_info:
            count = speaker_info.get("count", "?")
            s_list = speaker_info.get("list", [])
            
            s_frame = ctk.CTkFrame(self, fg_color="transparent")
            s_frame.pack(fill="x", padx=40, pady=(0, 20))
            
            ctk.CTkLabel(s_frame, text=f"Speakers detected ({count}):", font=("Arial", 14, "bold"), text_color=C_PURPLE).pack(side="left")
            
            # Simple list
            s_text = ", ".join(s_list)
            ctk.CTkLabel(s_frame, text=s_text, font=("Arial", 14), text_color="gray80").pack(side="left", padx=10)

        # Exec Summary
        self.add_section("Executive Summary", data.get("executive_summary", ""))
        
        # Highlights
        highlights = data.get("highlights", [])
        if highlights:
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=40, pady=10)
            ctk.CTkLabel(f, text="Key Highlights", font=("Arial", 18, "bold"), text_color=C_PURPLE).pack(anchor="w", pady=(0, 10))
            for h in highlights:
                ctk.CTkLabel(f, text=f"• {h}", font=("Arial", 14), text_color="white", wraplength=800, justify="left").pack(anchor="w", pady=2)

        # Full Sections
        sections = data.get("full_summary_sections", [])
        for sec in sections:
            self.add_section(
                sec.get("header", "Topic"), 
                sec.get("content", ""), 
                quote=sec.get("quote"),
                attribution=sec.get("attribution")
            )

        # Tasks
        tasks = data.get("tasks", [])
        if tasks:
            f = ctk.CTkFrame(self, fg_color=C_CARD_BG, corner_radius=10)
            f.pack(fill="x", padx=40, pady=30)
            ctk.CTkLabel(f, text="Action Items", font=("Arial", 18, "bold"), text_color="white").pack(anchor="w", padx=20, pady=20)
            for t in tasks:
                desc = t.get('description', str(t))
                assignee = t.get('assignee')
                if assignee: desc += f" ({assignee})"
                
                ctk.CTkCheckBox(f, text=desc, text_color="white", fg_color=C_PURPLE).pack(anchor="w", padx=20, pady=5)
            ctk.CTkLabel(f, text="", height=10).pack()

        # Transcript
        self.add_section("Transcript", data.get("transcript", ""), collapsed=True)

    def add_section(self, title, content, quote=None, collapsed=False, attribution=None):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=15)
        
        # Header Row
        h = ctk.CTkFrame(f, fg_color="transparent")
        h.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(h, text=title, font=("Arial", 18, "bold"), text_color="white").pack(side="left")
        
        if attribution:
            ctk.CTkLabel(h, text=f"({attribution})", font=("Arial", 14, "italic"), text_color=C_PURPLE).pack(side="left", padx=10)
        
        if quote:
             q_frame = ctk.CTkFrame(f, fg_color="#2B2B2B", corner_radius=5, border_width=0, border_color=C_PURPLE)
             q_frame.pack(fill="x", pady=(0, 10))
             # Left border simulation
             l = ctk.CTkFrame(q_frame, width=4, fg_color=C_PURPLE)
             l.pack(side="left", fill="y")
             ctk.CTkLabel(q_frame, text=f'"{quote}"', font=("Arial", 13, "italic"), text_color="gray80", wraplength=750, justify="left").pack(side="left", padx=10, pady=10)

        if content:
            ctk.CTkLabel(f, text=content, font=("Arial", 14), text_color="gray90", wraplength=800, justify="left", height=100 if collapsed else 0).pack(anchor="w")
