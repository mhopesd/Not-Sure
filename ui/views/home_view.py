import customtkinter as ctk
from ui.styles import *

class HomeView(ctk.CTkFrame):
    def __init__(self, parent, open_callback, history):
        super().__init__(parent, fg_color=C_BG_DARK, corner_radius=0)
        self.grid(row=0, column=0, sticky="nsew")
        self.open_callback = open_callback
        
        # Compact Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(30, 20), padx=30, fill="x") # Reduced padding
        ctk.CTkLabel(header, text="Good evening, Michael", font=("Arial", 28, "bold"), text_color="white").pack(anchor="w")
        subtitle = "You're caught up" if not history else f"You have {len(history)} recordings"
        ctk.CTkLabel(header, text=subtitle, font=("Arial", 14), text_color="gray60").pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(self, text="Recently recorded", font=("Arial", 13), text_color="gray60", anchor="w").pack(padx=30, pady=(0, 10), fill="x")
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20) # Reduced horizontal padding for cards

        if not history:
             ctk.CTkLabel(scroll_frame, text="No recordings yet.", text_color="gray50").pack(pady=20)
        else:
            for item in history[:5]:
                self.create_meeting_card(scroll_frame, item)

    def create_meeting_card(self, parent, item):
        title = item.get("title", "Untitled Meeting")
        date = item.get("date", item.get("timestamp", ""))
        duration = item.get("duration", "")
        
        display_date = date
        if duration:
            display_date = f"{date} • {duration}"

        summary = item.get("executive_summary", "No summary available.")
        
        card = ctk.CTkFrame(parent, fg_color=C_CARD_BG, corner_radius=10, border_width=1, border_color=C_BORDER)
        card.pack(fill="x", pady=5, padx=5)
        
        # Make card clickable
        for widget in [card] + card.winfo_children():
            # Note: binding to child widgets might need recursive apply later if complexity grows
            pass
        
        # Title Row
        h_frame = ctk.CTkFrame(card, fg_color="transparent")
        h_frame.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(h_frame, text=title, font=("Arial", 16, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(h_frame, text=display_date, font=("Arial", 12), text_color="gray50").pack(side="right")
        
        # Summary
        ctk.CTkLabel(card, text=summary[:150] + "...", font=("Arial", 13), text_color="gray70", anchor="w", wraplength=800, justify="left").pack(padx=15, pady=(0, 15), fill="x")
        
        # Click handler (Overlay button or bind)
        btn = ctk.CTkButton(card, text="View Details", fg_color="transparent", border_width=1, border_color=C_BORDER, hover_color="#2B2B2B", height=30,
                            command=lambda: self.open_callback(item))
        btn.pack(padx=15, pady=(0, 15), anchor="e")
