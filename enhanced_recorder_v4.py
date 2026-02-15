#!/usr/bin/env python3
"""
Audio Summary App - CLI Version
Uses shared backend.py logic.
"""
import time
import sys
import threading
from backend import EnhancedAudioApp

class CLIApp:
    def __init__(self):
        self.app = EnhancedAudioApp(
            status_callback=self.print_status,
            result_callback=self.show_result
        )

    def print_status(self, msg):
        # precise overwriting could be done with \r but simple print is safer for now
        print(f"[STATUS] {msg}")

    def show_result(self, data):
        print("\n" + "="*60)
        print("SUMMARY RESULT")
        print("="*60)
        if isinstance(data, dict):
            print(f"Title: {data.get('title')}")
            print(f"Executive Summary: {data.get('executive_summary')}")
            # Print other fields as needed
        else:
            print(data)
        print("="*60 + "\n")

    def show_menu(self):
        while True:
            print(f"\nMode: {self.app.recording_mode} | LLM: {self.app.config['SETTINGS'].get('default_llm', 'auto')}")
            print("1. Record | 2. Mode | 3. Config Gemini Key | 4. History | 5. Exit")
            choice = input("Choice: ").strip()
            
            if choice == '1': 
                self.recording_workflow()
            elif choice == '2': 
                self.change_mode()
            elif choice == '3':
                k = input("Gemini Key: ").strip()
                if k: 
                    self.app.config['API_KEYS']['gemini'] = k
                    # Save config manually since backend handles loading mostly
                    with open(self.app.config_file, 'w') as f: 
                        self.app.config.write(f)
                    print("Key saved.")
            elif choice == '4': 
                self.view_history()
            elif choice == '5': 
                break

    def change_mode(self):
        print("1. Microphone | 2. System Audio (BlackHole) | 3. Hybrid")
        c = input("Select: ").strip()
        mode_map = {'1': "Microphone", '2': "System Audio", '3': "Hybrid"}
        if c in mode_map:
            self.app.set_mode(mode_map[c])
        else:
            print("Invalid selection")

    def recording_workflow(self):
        print("\nPress ENTER to start recording... (Ctrl+C to stop)")
        input()
        self.app.start_recording()
        try:
            print("● RECORDING... Press Ctrl+C to stop")
            while self.app.is_recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.app.stop_recording()
            # Wait for processing to happen (callbacks will print)
            while threading.active_count() > 1: # approximate check for bg threads
                 time.sleep(0.5)
                 if not self.app.transcription_thread.is_alive() and not self.app.recording_thread.is_alive():
                     break
            print("Recording workflow finished.")

    def view_history(self):
        hist = self.app.chat_history
        if not hist:
            print("No history found.")
            return
        for i, e in enumerate(hist[:5]):
            ts = e.get('timestamp', 'N/A')
            summ = e.get('executive_summary', e.get('full_summary', 'No summary'))[:50]
            print(f"{i+1}. {ts} - {summ}...")

if __name__ == "__main__":
    cli = CLIApp()
    cli.show_menu()
