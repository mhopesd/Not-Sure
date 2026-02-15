#!/usr/bin/env python3
"""
Audio Summary App - Version with Chat History
Records audio, transcribes it locally with Whisper, and summarizes with Ollama
Includes chat history functionality to save and browse previous recordings
"""

import threading
import queue
import wave
import pyaudio
import json
import requests
import whisper
import os
import tempfile
from datetime import datetime
import dearpygui.dearpygui as dpg


class AudioSummaryApp:
    def __init__(self):
        dpg.create_context()
        
        # Audio recording variables
        self.is_recording = False
        self.recording_thread = None
        self.temp_audio_file = None
        
        # Load Whisper model (lazy loading)
        self.whisper_model = None
        
        # Chat history
        self.history_file = "audio_history.json"
        self.chat_history = []
        self.current_session_id = None
        self.selected_history_id = None
        
        # Load existing history
        self.load_history()
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        dpg.create_viewport(title="Audio Summary App", width=1000, height=700)
        
        with dpg.window(label="Audio Summary App", tag="main_window", no_title_bar=True, no_move=True, no_resize=True):
            # Title
            dpg.add_text("Audio Summary App", tag="title")
            dpg.add_separator()
            
            # Control buttons
            with dpg.group(horizontal=True):
                self.record_button = dpg.add_button(
                    label="Start Recording", 
                    callback=self.toggle_recording,
                    width=150,
                    tag="record_button"
                )
                
                # Status text
                self.status_text_widget = dpg.add_text("Ready to record", tag="status", color=[100, 255, 100])
            
            dpg.add_spacer(height=10)
            
            # Tab bar for main sections and history
            with dpg.tab_bar(tag="tabs"):
                # Current Session Tab
                with dpg.tab(label="Current Session"):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Current Recording:")
                        dpg.add_spacer(width=-1)
                    
                    # Transcript section
                    dpg.add_separator()
                    dpg.add_text("Transcript:", color=[150, 150, 255])
                    dpg.add_input_text(
                        multiline=True,
                        default_value="",
                        width=-1,
                        height=200,
                        readonly=True,
                        tag="transcript_text"
                    )
                    
                    # Summary section
                    dpg.add_separator()
                    dpg.add_text("Summary:", color=[150, 255, 150])
                    dpg.add_input_text(
                        multiline=True,
                        default_value="",
                        width=-1,
                        height=200,
                        readonly=True,
                        tag="summary_text"
                    )
                
                # History Tab
                with dpg.tab(label="Chat History"):
                    # History controls
                    with dpg.group(horizontal=True):
                        dpg.add_text("Previous Recordings:")
                        dpg.add_spacer(width=50)
                        dpg.add_button(label="Clear All History", callback=self.clear_history, width=120)
                    
                    dpg.add_separator()
                    
                    # History list and details
                    with dpg.group(horizontal=True):
                        # History list (left side)
                        with dpg.child_window(label="History List", width=300, height=500, border=True):
                            self.history_list = dpg.add_listbox(
                                items=[],
                                num_items_visible=15,
                                callback=self.on_history_select
                            )
                        
                        # History details (right side)
                        with dpg.child_window(label="History Details", width=-1, height=500, border=True):
                            dpg.add_text("Select a recording to view details", tag="history_title")
                            dpg.add_separator()
                            
                            dpg.add_text("Transcript:", color=[150, 150, 255], tag="history_transcript_label")
                            self.history_transcript = dpg.add_input_text(
                                multiline=True,
                                default_value="",
                                width=-1,
                                height=180,
                                readonly=True,
                                tag="history_transcript"
                            )
                            
                            dpg.add_separator()
                            
                            dpg.add_text("Summary:", color=[150, 255, 150], tag="history_summary_label")
                            self.history_summary = dpg.add_input_text(
                                multiline=True,
                                default_value="",
                                width=-1,
                                height=180,
                                readonly=True,
                                tag="history_summary"
                            )
        
        dpg.set_primary_window("main_window", True)
        
        # Update history list
        self.update_history_list()
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio from the microphone"""
        self.is_recording = True
        dpg.set_value("record_button", "Stop & Process")
        dpg.set_value("status", "Recording...")
        
        # Clear previous content
        dpg.set_value("transcript_text", "")
        dpg.set_value("summary_text", "")
        
        # Generate new session ID
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop recording and process the audio"""
        self.is_recording = False
        dpg.set_value("record_button", "Processing...")
        dpg.configure_item("record_button", enabled=False)
        dpg.set_value("status", "Processing audio...")
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        # Process the recorded audio in a separate thread
        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.start()
    
    def record_audio(self):
        """Record audio from the microphone"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        # Create temporary file for audio
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_audio_file = os.path.join(temp_dir, f"audio_recording_{timestamp}.wav")
        
        p = pyaudio.PyAudio()
        
        try:
            # Try to find the default input device
            device_info = None
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_info = info
                    break
            
            # Use default device settings if specific device not found
            input_device = device_info['index'] if device_info else None
            
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          input_device_index=input_device,
                          frames_per_buffer=CHUNK)
            
            frames = []
            
            while self.is_recording:
                data = stream.read(CHUNK)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save the recorded data as a WAV file
            with wave.open(self.temp_audio_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                
        finally:
            p.terminate()
    
    def load_whisper_model(self):
        """Load Whisper model if not already loaded"""
        if self.whisper_model is None:
            dpg.set_value("status", "Loading Whisper model...")
            dpg.set_value("status", "Ready to record")
            self.whisper_model = whisper.load_model("base")
    
    def process_audio(self):
        """Transcribe and summarize the recorded audio"""
        try:
            # Load Whisper model
            self.load_whisper_model()
            
            # Transcribe audio
            dpg.set_value("status", "Transcribing audio...")
            
            result = self.whisper_model.transcribe(self.temp_audio_file)
            transcript = result["text"]
            
            # Display transcript
            dpg.set_value("transcript_text", transcript)
            
            # Generate summary
            dpg.set_value("status", "Generating summary...")
            
            summary = self.generate_summary(transcript)
            
            # Display summary
            dpg.set_value("summary_text", summary)
            
            # Save to history
            if self.current_session_id:
                self.save_to_history(self.current_session_id, transcript, summary)
            
        except Exception as e:
            error_message = f"Error processing audio: {str(e)}"
            dpg.set_value("summary_text", error_message)
        
        finally:
            # Clean up temporary audio file
            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
                self.temp_audio_file = None
            
            # Reset UI
            dpg.set_value("status", "Ready to record")
            dpg.set_value("record_button", "Start Recording")
            dpg.configure_item("record_button", enabled=True)
    
    def generate_summary(self, transcript):
        """Generate summary using Ollama"""
        try:
            url = "http://localhost:11434/api/generate"
            
            prompt = f"""You are an expert assistant who summarizes conversations. Please provide a concise summary of the following transcript. Focus on key decisions, main topics, and any action items mentioned.

Transcript:
"{transcript}"

Summary:"""
            
            payload = {
                "model": "llama3:8b",
                "stream": False,
                "prompt": prompt
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No summary generated")
            
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Please ensure Ollama is running on localhost:11434"
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def save_to_history(self, session_id, transcript, summary):
        """Save a recording to history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create entry
        entry = {
            "session_id": session_id,
            "timestamp": timestamp,
            "transcript": transcript,
            "summary": summary
        }
        
        # Add to history (at the beginning)
        self.chat_history.insert(0, entry)
        
        # Keep only last 50 entries to prevent file from getting too large
        if len(self.chat_history) > 50:
            self.chat_history = self.chat_history[:50]
        
        # Save to file
        self.save_history()
        
        # Update UI
        self.update_history_list()
    
    def load_history(self):
        """Load chat history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            self.chat_history = []
    
    def save_history(self):
        """Save chat history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def update_history_list(self):
        """Update the history list in the UI"""
        if not dpg.does_item_exist("history_list"):
            return
            
        # Extract display items for listbox
        display_items = []
        for entry in self.chat_history:
            display_time = entry.get('timestamp', 'Unknown')
            summary_preview = entry.get('summary', 'No summary')[:60]
            if len(summary_preview) == 60:
                summary_preview += "..."
            display_items.append(f"{display_time} - {summary_preview}")
        
        dpg.configure_item("history_list", items=display_items)
    
    def on_history_select(self):
        """Handle history item selection"""
        if not dpg.does_item_exist("history_list"):
            return
            
        selected_indices = dpg.get_value("history_list")
        if not selected_indices:
            return
        
        index = selected_indices
        if 0 <= index < len(self.chat_history):
            entry = self.chat_history[index]
            self.selected_history_id = entry['session_id']
            
            # Update details view
            timestamp = entry.get('timestamp', 'Unknown')
            dpg.set_value("history_title", f"Recording from {timestamp}")
            dpg.set_value("history_transcript", entry.get('transcript', 'No transcript'))
            dpg.set_value("history_summary", entry.get('summary', 'No summary'))
    
    def clear_history(self):
        """Clear all history"""
        self.chat_history = []
        self.save_history()
        self.update_history_list()
        
        # Clear details view
        dpg.set_value("history_title", "Select a recording to view details")
        dpg.set_value("history_transcript", "")
        dpg.set_value("history_summary", "")
        self.selected_history_id = None
    
    def run(self):
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    app = AudioSummaryApp()
    app.run()