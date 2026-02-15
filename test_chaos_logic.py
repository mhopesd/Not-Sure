import unittest
import os
import time
from chaos_engineering import ChaosMonkey, ErrorMonitor

# Mock Class matching the interface we care about
class MockAudioApp:
    def start_recording(self):
        print("Real start_recording called")
        return "Started"

    def process_audio(self):
        print("Real process_audio called")
        return "Processed"
        
    def generate_summary(self):
        print("Real generate_summary called")
        return "Summary"

class TestChaos(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_chaos_report.log"
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            
        self.monitor = ErrorMonitor(log_file=self.log_file)
        # Probability 1.0 to ensure it ALWAYS happens for test
        self.chaos = ChaosMonkey(self.monitor, probability=1.0) 
        self.app = MockAudioApp()
        self.chaos.apply_patches(self.app)

    def test_start_recording_injection(self):
        print("\nTesting start_recording injection...")
        with self.assertRaises(OSError) as cm:
            self.app.start_recording()
        print(f"Caught expected error: {cm.exception}")
        self.assertTrue("Microphone device not accessible" in str(cm.exception))

    def test_process_audio_injection(self):
        print("\nTesting process_audio injection...")
        with self.assertRaises(ValueError) as cm:
            self.app.process_audio()
        print(f"Caught expected error: {cm.exception}")
        self.assertTrue("Corrupt audio buffer detected" in str(cm.exception))

    def test_log_file_creation(self):
        # Trigger one error
        try:
            self.app.start_recording()
        except:
            pass
        
        # Check log file exists and has content
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, 'r') as f:
            content = f.read()
            print("Log Content Preview:\n" + content[:200])
            self.assertTrue("FAILURE DETECTED" in content)
            self.assertTrue("Chaos Agent Triggered: True" in content)

if __name__ == '__main__':
    unittest.main()
