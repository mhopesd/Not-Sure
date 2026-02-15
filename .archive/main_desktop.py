#!/usr/bin/env python3
"""
Audio Summary App - Version using Dear PyGui
Records audio, transcribes it locally with Whisper, and summarizes with Ollama
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
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.temp_audio_file = None
        
        # Load Whisper model (lazy loading)
        self.whisper_model = None
        
        # UI state
        self.transcript_text = ""
        self.summary_text = ""
        self.status_text = "Ready to record"
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        dpg.create_viewport(title="Audio Summary App", width=800, height=600)
        
        with dpg.window(label="Audio Summary App", tag="main_window", no_title_bar=True, no_move=True, no_resize=True):
            # Title
            dpg.add_text("Audio Summary App")
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
            
            # Tab bar for transcript and summary
            with dpg.tab_bar(tag="tabs"):
                with dpg.tab(label="Transcript"):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Transcript:")
                        dpg.add_spacer(width=-1)
                    dpg.add_input_text(
                        multiline=True,
                        default_value="",
                        width=-1,
                        height=400,
                        readonly=True,
                        tag="transcript_text"
                    )
                
                with dpg.tab(label="Summary"):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Summary:")
                        dpg.add_spacer(width=-1)
                    dpg.add_input_text(
                        multiline=True,
                        default_value="",
                        width=-1,
                        height=400,
                        readonly=True,
                        tag="summary_text"
                    )
        
        dpg.set_primary_window("main_window", True)
        
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
        self.status_text = "Recording..."
        
        # Clear previous content
        dpg.set_value("transcript_text", "")
        dpg.set_value("summary_text", "")
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop recording and process the audio"""
        self.is_recording = False
        dpg.set_value("record_button", "Processing...")
        dpg.configure_item("record_button", enabled=False)
        dpg.set_value("status", "Processing audio...")
        self.status_text = "Processing audio..."
        
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
            self.status_text = "Loading Whisper model..."
            self.whisper_model = whisper.load_model("base")
    
    def process_audio(self):
        """Transcribe and summarize the recorded audio"""
        try:
            # Load Whisper model
            self.load_whisper_model()
            
            # Transcribe audio
            dpg.set_value("status", "Transcribing audio...")
            self.status_text = "Transcribing audio..."
            
            result = self.whisper_model.transcribe(self.temp_audio_file)
            transcript = result["text"]
            
            # Display transcript
            dpg.set_value("transcript_text", transcript)
            
            # Generate summary
            dpg.set_value("status", "Generating summary...")
            self.status_text = "Generating summary..."
            
            summary = self.generate_summary(transcript)
            
            # Display summary
            dpg.set_value("summary_text", summary)
            
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
            self.status_text = "Ready to record"
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
    
    def run(self):
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    app = AudioSummaryApp()
    app.run()