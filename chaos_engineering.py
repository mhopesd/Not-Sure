import logging
import random
import time
import functools
import traceback
import sys
import psutil
import threading
from datetime import datetime

# --- Monitor Agent ---
class ErrorMonitor:
    def __init__(self, log_file="chaos_report.log"):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        self.logger = logging.getLogger("MonitorAgent")
        self.logger.setLevel(logging.INFO)
        
        # File Handler for structured report
        fh = logging.FileHandler(self.log_file, mode='w')
        fh.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(fh)
            
        self.logger.info("Monitor Agent Initialized. Watching for Chaos...")

    def log_failure(self, component, error_type, details, stack_trace, chaos_triggered=False):
        """
        Logs a detailed failure report.
        """
        system_stats = self._get_system_stats()
        
        report = (
            f"\n{'='*50}\n"
            f"FAILURE DETECTED in [{component}]\n"
            f"{'='*50}\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
            f"Chaos Agent Triggered: {chaos_triggered}\n"
            f"Error Type: {error_type}\n"
            f"Message: {details}\n"
            f"System State:\n"
            f"  - CPU Usage: {system_stats['cpu']}%\n"
            f"  - Memory Used: {system_stats['memory_used']} MB\n"
            f"  - Active Threads: {system_stats['threads']}\n"
            f"Stack Trace:\n{stack_trace}\n"
            f"{'='*50}\n"
        )
        self.logger.error(report)
        print(f"[MonitorAgent] Captured crash in {component}. See {self.log_file}")

    def _get_system_stats(self):
        process = psutil.Process()
        return {
            "cpu": psutil.cpu_percent(interval=None),
            "memory_used": round(process.memory_info().rss / 1024 / 1024, 2),
            "threads": threading.active_count()
        }

# --- Chaos Agent ---
class ChaosMonkey:
    def __init__(self, monitor_agent, probability=0.3):
        self.monitor = monitor_agent
        self.probability = probability
        self.active = True
        self.logger = logging.getLogger("ChaosMonkey")

    def should_disrupt(self):
        return self.active and random.random() < self.probability

    def inject_latency(self):
        """Sleeps for a random time to simulate lag."""
        if self.should_disrupt():
            delay = random.uniform(0.5, 3.0)
            self.logger.warning(f"Injecting {delay:.2f}s latency...")
            time.sleep(delay)

    def disrupt_method(self, method_name, exception_to_raise, message):
        """
        Decorator-like wrapper logic to inject errors.
        """
        if self.should_disrupt():
            error_msg = f"[CHAOS INJECTION] {message}"
            self.logger.warning(f"Sabotaging {method_name}: {error_msg}")
            
            # Notify Monitor that WE caused this
            try:
                raise exception_to_raise(error_msg)
            except Exception as e:
                self.monitor.log_failure(
                    component=method_name,
                    error_type=type(e).__name__,
                    details=str(e),
                    stack_trace=traceback.format_exc(),
                    chaos_triggered=True
                )
                raise # Re-raise so the app actually fails

    def apply_patches(self, target_object):
        """
        Monkey-patches methods on the target object to inject chaos.
        """
        self.logger.info(f"Unleashing Chaos Monkey on {target_object.__class__.__name__}")
        
        # 1. Patch start_recording (Simulate Device Errors)
        original_start = target_object.start_recording
        @functools.wraps(original_start)
        def patched_start(*args, **kwargs):
            self.disrupt_method("start_recording", OSError, "Microphone device not accessible")
            self.inject_latency()
            return original_start(*args, **kwargs)
        target_object.start_recording = patched_start
        
        # 2. Patch process_audio (Simulate Processing Failures)
        original_process = target_object.process_audio
        @functools.wraps(original_process)
        def patched_process(*args, **kwargs):
            self.disrupt_method("process_audio", ValueError, "Corrupt audio buffer detected")
            return original_process(*args, **kwargs)
        target_object.process_audio = patched_process

        # 3. Patch generate_summary (Simulate API/LLM Failures)
        original_generate = target_object.generate_summary
        @functools.wraps(original_generate)
        def patched_generate(*args, **kwargs):
            self.disrupt_method("generate_summary", ConnectionError, "LLM Service Unreachable (Timeout)")
            return original_generate(*args, **kwargs)
        target_object.generate_summary = patched_generate

        self.logger.info("Patches applied.")
