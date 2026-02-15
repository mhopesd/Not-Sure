
import customtkinter as ctk
import threading
import wave
import pyaudio
import json
import requests
import whisper
import os
import tempfile
from datetime import datetime
import sys
import configparser
import queue
import numpy as np

# Try to import Google GenAI
try:
    from google import genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

# --- Theme Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- COLORS (Extracted from Screenshots) ---
C_BG_DARK = "#121212"        # Main Background
C_SIDEBAR = "#1E1E1E"        # Sidebar Background
C_CARD_BG = "#1E1E1E"        # Card Background
C_PURPLE = "#8A2BE2"         # "Start Jamie" Purple
C_PURPLE_HOVER = "#7B1FA2"
C_TEXT_MAIN = "#FFFFFF"
C_TEXT_SUB = "#A0A0A0"
C_BORDER = "#2B2B2B"

class EnhancedAudioApp:
    def __init__(self, status_callback=None, result_callback=None):
        self.is_recording = False
        self.recording_thread = None
        self.temp_audio_file = None
        self.recording_mode = "microphone"
        
        self.devices = {}
        self.blackhole_device = None
        self.microphone_device = None
        self.whisper_model = None
        
        self.mic_queue = queue.Queue()
        self.sys_queue = queue.Queue()
        
        self.config_file = "audio_config.ini"
        self.history_file = "audio_history.json"
        self.history_directory = os.path.expanduser("~/Documents/Audio Recordings")
        
        self.config = configparser.ConfigParser()
        self.load_config()
        
        self.chat_history = []
        self.load_history()

        self.status_callback = status_callback
        self.result_callback = result_callback
        
        self.detect_devices()

        
    def update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def load_config(self):
        self.config['API_KEYS'] = {'openai': '', 'anthropic': '', 'gemini': ''}
        self.config['SETTINGS'] = {
            'history_directory': os.path.expanduser("~/Documents/Audio Recordings"),
            'default_llm': 'auto', 'ollama_model': 'llama3:8b'
        }
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                self.history_directory = self.config['SETTINGS'].get('history_directory', self.history_directory)
            self.auto_detect_llm()
        except Exception as e: self.update_status(f"Config warning: {e}")

    def auto_detect_llm(self):
        llm_priority = ['openai', 'gemini', 'anthropic', 'ollama']
        if self.config['SETTINGS'].get('default_llm', 'auto') == 'auto':
            for llm in llm_priority:
                if llm == 'ollama':
                    self.config['SETTINGS']['default_llm'] = 'ollama'; break
                elif self.config['API_KEYS'].get(llm):
                    self.config['SETTINGS']['default_llm'] = llm; break

    def save_config(self):
        try:
            self.config['SETTINGS']['history_directory'] = self.history_directory
            with open(self.config_file, 'w') as f: self.config.write(f)
        except: pass

    def create_history_directory(self):
        try: os.makedirs(self.history_directory, exist_ok=True)
        except: self.history_directory = os.getcwd()

    def detect_devices(self):
        p = pyaudio.PyAudio()
        try:
            self.update_status("Detecting audio devices...")
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                name = info['name'].lower()
                
                if 'blackhole' in name:
                    self.blackhole_device = {'index': i, 'name': info['name'], 'channels': info['maxInputChannels']}
                    self.update_status(f"✓ Found BlackHole: {info['name']}")
                
                if info['maxInputChannels'] > 0 and 'blackhole' not in name:
                    if not self.microphone_device:
                        self.microphone_device = {'index': i, 'name': info['name'], 'channels': info['maxInputChannels']}
                        self.update_status(f"✓ Found Microphone: {info['name']}")
            
            if not self.blackhole_device:
                self.update_status("! BlackHole not found. System audio recording disabled.")
        finally:
            p.terminate()

    def start_recording(self):
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
        self.update_status("● RECORDING...")

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        
        self.update_status("Processing audio...")
        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.start()

    def record_audio(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        RATE = 44100
        temp_dir = tempfile.gettempdir()
        self.temp_audio_file = os.path.join(temp_dir, f"rec_{datetime.now().strftime('%H%M%S')}.wav")
        p = pyaudio.PyAudio()
        try:
            if self.recording_mode == 'hybrid' and self.blackhole_device:
                self.record_dual_device(p, FORMAT, RATE, CHUNK)
            else:
                dev = self.blackhole_device if self.recording_mode == 'system' else self.microphone_device
                self.record_single_device(p, dev, FORMAT, RATE, CHUNK)
        finally:
            p.terminate()

    def record_single_device(self, p, device, FORMAT, RATE, CHUNK):
        if not device: return
        stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, input_device_index=device['index'], frames_per_buffer=CHUNK)
        frames = []
        while self.is_recording: frames.append(stream.read(CHUNK))
        stream.stop_stream(); stream.close()
        with wave.open(self.temp_audio_file, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(p.get_sample_size(FORMAT)); wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

    def record_dual_device(self, p, FORMAT, RATE, CHUNK):
        self.mic_queue = queue.Queue(); self.sys_queue = queue.Queue()
        mic_stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, input_device_index=self.microphone_device['index'], frames_per_buffer=CHUNK)
        sys_stream = p.open(format=FORMAT, channels=2, rate=RATE, input=True, input_device_index=self.blackhole_device['index'], frames_per_buffer=CHUNK)
        
        def read_stream(stream, q):
            while self.is_recording:
                try: q.put(stream.read(CHUNK, exception_on_overflow=False))
                except: break
            q.put(None)

        t1 = threading.Thread(target=read_stream, args=(mic_stream, self.mic_queue))
        t2 = threading.Thread(target=read_stream, args=(sys_stream, self.sys_queue))
        t1.start(); t2.start()

        frames = []
        active = 2
        while active > 0:
            try: m = self.mic_queue.get(timeout=1)
            except: m = b'\x00'*CHUNK*2
            try: s = self.sys_queue.get(timeout=1)
            except: s = b'\x00'*CHUNK*4
            
            if m is None: active-=1; continue
            if s is None: active-=1; continue
            
            if len(m) > 0 and len(s) > 0:
                s_arr = np.frombuffer(s, dtype=np.int16)
                s_mono = (s_arr[0::2] + s_arr[1::2]) // 2
                m_arr = np.frombuffer(m, dtype=np.int16)
                min_len = min(len(m_arr), len(s_mono))
                mixed = m_arr[:min_len].astype(np.int32) + s_mono[:min_len].astype(np.int32)
                frames.append(np.clip(mixed, -32768, 32767).astype(np.int16).tobytes())

        t1.join(); t2.join()
        mic_stream.stop_stream(); mic_stream.close()
        sys_stream.stop_stream(); sys_stream.close()
        
        with wave.open(self.temp_audio_file, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def process_audio(self):
        if not self.temp_audio_file or not os.path.exists(self.temp_audio_file):
            self.update_status("Error: No audio file to process.")
            return

        self.update_status("Transcribing...")
        if not self.whisper_model:
            self.whisper_model = whisper.load_model("base")
        
        result = self.whisper_model.transcribe(self.temp_audio_file)
        
        formatted_transcript = ""
        for segment in result['segments']:
            start = self.format_time(segment['start'])
            end = self.format_time(segment['end'])
            text = segment['text'].strip()
            formatted_transcript += f"Speaker:\n{start} - {end}\n{text}\n\n"
            
        self.update_status(f"Transcription complete.")
        
        self.update_status("Generating summary...")
        summary = self.generate_summary(formatted_transcript)
        
        self.update_status("Summary complete.")
        
        self.save_to_history(formatted_transcript, summary)

        if self.result_callback:
            self.result_callback(formatted_transcript, summary)

    def generate_summary(self, transcript):
        llm = self.config['SETTINGS'].get('default_llm', 'ollama')
        if llm == 'gemini': return self._summarize_with_gemini(transcript)
        # Add other LLM logic here if needed, for now, we'll just print to console
        print(f"Using {llm} for summarization (not implemented in GUI yet)")
        return "Summary generation for this LLM is not yet implemented in the GUI."

    def _summarize_with_gemini(self, transcript):
        if not GOOGLE_GENAI_AVAILABLE: return "Google GenAI library is missing."
        key = self.config['API_KEYS'].get('gemini')
        if not key: return "Gemini API key not found in audio_config.ini"
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            system_instruction = """
            You are an expert executive assistant. Process the meeting transcript into a structured report following this exact format:

            EXECUTIVE SUMMARY
            (A high-level paragraph summarizing the core business value, metrics, and outcomes. Put the most important numbers here.)

            KEY HIGHLIGHTS
            • (Bullet point of critical takeaway 1)
            • (Bullet point of critical takeaway 2)
            • (Bullet point of critical takeaway 3)

            ________________________________________________________________________________

            [TOPIC 1 HEADER]
            (Summary of the discussion regarding this topic)
            > "Insert a direct, verbatim quote from the transcript that supports this."

            [TOPIC 2 HEADER]
            (Summary of the discussion regarding this topic)
            > "Insert a direct, verbatim quote from the transcript that supports this."

            ACTION ITEMS
            [ ] Task 1
            [ ] Task 2
            """
            
            response = model.generate_content(f"{system_instruction}\n\nTRANSCRIPT:\n{transcript}")
            return response.text
        except Exception as e: return f"Gemini Error: {e}"

    def save_to_history(self, t, s):
        self.chat_history.insert(0, {"timestamp": str(datetime.now()), "transcript": t, "summary": s})
        with open(self.history_file, 'w') as f: json.dump(self.chat_history, f, indent=4)
    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f: self.chat_history = json.load(f)

class AudioSummaryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Audio Summary App")
        self.geometry("1300x850")
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar() 
        self.audio_app = EnhancedAudioApp(status_callback=self.update_status_bar, result_callback=self.display_results)
        
        self.create_main_content_area()
        
        self.show_view("detail")

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=C_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.pack(pady=30, padx=20, fill="x")
        ctk.CTkLabel(self.logo_frame, text="AS", width=30, height=30, fg_color="#4CAF50", corner_radius=5, text_color="white", font=("Arial", 14, "bold")).pack(side="left")
        ctk.CTkLabel(self.logo_frame, text="Audio Summary", font=("Arial", 16, "bold"), text_color="white").pack(side="left", padx=10)

        self.rec_btn = ctk.CTkButton(self.sidebar, text="⚡ Start Recording", fg_color=C_PURPLE, hover_color=C_PURPLE_HOVER, height=45, font=("Arial", 15, "bold"), command=self.toggle_recording)
        self.rec_btn.pack(padx=20, pady=(0, 10), fill="x")
        
        self.status_bar = ctk.CTkLabel(self.sidebar, text="Ready", text_color="gray70", font=("Arial", 12))
        self.status_bar.pack(padx=20, pady=(0, 20), fill="x")
        
        # Simplified sidebar
        ctk.CTkLabel(self.sidebar, text="Recording Mode", text_color="gray50", anchor="w", font=("Arial", 12)).pack(padx=20, pady=(30, 10), fill="x")
        self.mode_selector = ctk.CTkSegmentedButton(self.sidebar, values=["Mic", "System", "Hybrid"], command=self.change_mode)
        self.mode_selector.set("Mic")
        self.mode_selector.pack(padx=20, fill="x")


    def create_main_content_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color=C_BG_DARK, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.views = {
            "detail": MeetingDetailView(self.main_container)
        }
        
        self.views["detail"].grid(row=0, column=0, sticky="nsew")


    def toggle_recording(self):
        if not self.audio_app.is_recording:
            self.audio_app.start_recording()
            self.rec_btn.configure(text="⏹️ Stop Recording", fg_color="red")
        else:
            self.audio_app.stop_recording()
            self.rec_btn.configure(text="⚡ Start Recording", fg_color=C_PURPLE)

    def change_mode(self, value):
        mode_map = {"Mic": "microphone", "System": "system", "Hybrid": "hybrid"}
        self.audio_app.recording_mode = mode_map.get(value.lower(), "microphone")
        if "system" in self.audio_app.recording_mode or "hybrid" in self.audio_app.recording_mode:
            if not self.audio_app.blackhole_device:
                self.update_status_bar("BlackHole device not found.")
                self.mode_selector.set("Mic")
                self.audio_app.recording_mode = "microphone"
        self.update_status_bar(f"Mode changed to {self.audio_app.recording_mode}")


    def update_status_bar(self, message):
        self.status_bar.configure(text=message)

    def display_results(self, transcript, summary):
        self.show_view("detail")
        detail_view = self.views.get("detail")
        if detail_view:
            detail_view.update_content(transcript, summary)

    def show_view(self, view_name):
        frame = self.views.get(view_name)
        if frame:
            frame.tkraise()


class MeetingDetailView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=C_BG_DARK, corner_radius=0)
        
        # Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(30, 5))

        # Left side of header (breadcrumbs and title)
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(left_header, text="Meetings  >  New Recording", text_color="gray60", anchor="w").pack(fill="x")
        ctk.CTkLabel(left_header, text="Meeting Notes", font=("Arial", 32, "bold"), text_color="white").pack(anchor="w")

        # Right side of header (toggle switch)
        right_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_header.pack(side="right")

        ctk.CTkLabel(right_header, text="Transcript", font=("Arial", 14)).pack(side="left", padx=10)
        self.view_switch = ctk.CTkSwitch(right_header, text="", command=self.toggle_view, onvalue="transcript", offvalue="summary")
        self.view_switch.pack(side="left")
        ctk.CTkLabel(right_header, text="Summary", font=("Arial", 14)).pack(side="left", padx=10)
        self.view_switch.select() # Default to Transcript

        # Textboxes container
        textbox_container = ctk.CTkFrame(self, fg_color="transparent")
        textbox_container.pack(fill="both", expand=True, padx=40, pady=20)
        textbox_container.grid_columnconfigure(0, weight=1)
        textbox_container.grid_rowconfigure(0, weight=1)

        self.summary_box = ctk.CTkTextbox(textbox_container, font=("Arial", 14), text_color="#E0E0E0", fg_color="#1a1a1a", wrap="word")
        self.summary_box.grid(row=0, column=0, sticky="nsew")
        
        self.trans_box = ctk.CTkTextbox(textbox_container, font=("Consolas", 13), text_color="#A0A0A0", fg_color="#1a1a1a", wrap="word")
        self.trans_box.grid(row=0, column=0, sticky="nsew")

        self.toggle_view()

    def toggle_view(self):
        if self.view_switch.get() == "summary":
            self.summary_box.tkraise()
        else:
            self.trans_box.tkraise()

    def update_content(self, transcript, summary):
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("1.0", summary)
        
        self.trans_box.delete("1.0", "end")
        self.trans_box.insert("1.0", transcript)


if __name__ == "__main__":
    app = AudioSummaryApp()
    app.mainloop()
