#!/usr/bin/env python3
"""
Audio Summary App - v4 (Device Selection Fix)
"""
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

class EnhancedAudioApp:
    def __init__(self):
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
        
        self.detect_devices()
        
        print("\n" + "="*60)
        print(" Audio Summary App - v4 (Final Device Fix)")
        print("="*60)
        
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
        except Exception as e: print(f"Config warning: {e}")

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
            print("\nDetecting audio devices...")
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                name = info['name'].lower()
                
                # 1. Look for BlackHole explicitly
                if 'blackhole' in name:
                    self.blackhole_device = {'index': i, 'name': info['name'], 'channels': info['maxInputChannels']}
                    print(f"✓ Found BlackHole: {info['name']}")
                
                # 2. Look for Microphone (BUT IGNORE BLACKHOLE)
                # This fixes the bug where BlackHole was selected as Mic
                if info['maxInputChannels'] > 0 and 'blackhole' not in name:
                    # Prefer "MacBook Pro Microphone" or "External Microphone"
                    # If we haven't found a mic yet, take this one
                    if not self.microphone_device:
                        self.microphone_device = {'index': i, 'name': info['name'], 'channels': info['maxInputChannels']}
                        print(f"✓ Found Microphone: {info['name']}")
            
            if not self.blackhole_device:
                print("! BlackHole not found. (Check System Settings > Privacy & Security)")
        finally:
            p.terminate()

    def show_menu(self):
        while True:
            print(f"\nMode: {self.recording_mode} | LLM: {self.config['SETTINGS']['default_llm']}")
            print("1. Record | 2. Mode | 3. Config LLM | 4. History | 5. Exit")
            choice = input("Choice: ").strip()
            if choice == '1': self.recording_workflow()
            elif choice == '2': self.change_recording_mode()
            elif choice == '3':
                k = input("Gemini Key: ");
                if k: self.config['API_KEYS']['gemini']=k; self.save_config()
            elif choice == '4': self.view_history()
            elif choice == '5': break

    def change_recording_mode(self):
        print("1. Mic | 2. System | 3. Hybrid")
        c = input("Select: ")
        if c=='1': self.recording_mode='microphone'
        if c=='2': self.recording_mode='system' if self.blackhole_device else 'microphone'
        if c=='3': self.recording_mode='hybrid' if self.blackhole_device else 'microphone'
        if not self.blackhole_device and c in ['2','3']: print("❌ BlackHole missing. Defaulting to Mic.")

    def recording_workflow(self):
        print("\nPress ENTER to start recording... (Ctrl+C to stop)")
        input()
        self.start_recording()
        try:
            print("● RECORDING... Press Ctrl+C to stop")
            while self.is_recording:
                import time; time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread: self.recording_thread.join()
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            self.process_audio()

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
        if not device: return # Safety check
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

    def process_audio(self):
        print("\nTranscribing...")
        if not self.whisper_model: self.whisper_model = whisper.load_model("base")
        result = self.whisper_model.transcribe(self.temp_audio_file)
        print(f"TRANSCRIPT: {result['text'][:100]}...")
        summary = self.generate_summary(result['text'])
        print(f"SUMMARY:\n{summary}")
        self.save_to_history(result['text'], summary)

    def generate_summary(self, transcript):
        llm = self.config['SETTINGS'].get('default_llm', 'ollama')
        if llm == 'gemini': return self._summarize_with_gemini(transcript)
        return "Unknown LLM"

    def _summarize_with_gemini(self, transcript):
        if not GOOGLE_GENAI_AVAILABLE: return "Lib missing"
        key = self.config['API_KEYS'].get('gemini')
        try:
            client = genai.Client(api_key=key)
            # UPDATED: Using gemini-2.0-flash which your diagnostic confirmed you have
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=f"Summarize this:\n{transcript}",
                config=types.GenerateContentConfig(temperature=0.2)
            )
            return response.text
        except Exception as e: return f"Gemini Error: {e}"

    def save_to_history(self, t, s):
        self.chat_history.insert(0, {"timestamp": str(datetime.now()), "transcript": t, "summary": s})
        with open(self.history_file, 'w') as f: json.dump(self.chat_history, f)
    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f: self.chat_history = json.load(f)
    def view_history(self):
        for i, e in enumerate(self.chat_history[:5]): print(f"{i+1}. {e['timestamp']} - {e['summary'][:50]}...")

if __name__ == "__main__":
    app = EnhancedAudioApp()
    app.show_menu()
