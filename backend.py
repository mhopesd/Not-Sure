import threading
import wave
import sounddevice as sd
import json
import os
import tempfile
from datetime import datetime
import configparser
import queue
import numpy as np
import re
import time
import shutil
import subprocess
import traceback
import requests
import uuid

# Use centralized logging
from app_logging import logger

# Secure credential storage (keychain)
from secure_store import secure_store

# Fix Google GenAI Import (New V1 SDK)
try:
    from google import genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    logger.warning("Google GenAI not installed (pip install google-genai).")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not installed (pip install openai).")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not installed (pip install anthropic).")

import whisper

class AudioCaptureError(Exception): pass

# --- Backend Logic (EnhancedAudioApp) ---
class EnhancedAudioApp:
    def __init__(self, status_callback=None, result_callback=None, transcript_callback=None, level_callback=None):
        self.is_recording = False
        self._processing_audio = False  # Guard against multiple stop_recording calls
        self.recording_thread = None
        self.transcription_thread = None
        self.temp_audio_file = None
        self.recording_mode = "microphone"
        self.recording_start_time = None
        self.recording_end_time = None 
        
        self.devices = {}
        self.blackhole_device = None
        self.microphone_device = None
        self.hybrid_device = None
        self.whisper_model = None
        self.model_loading = False
        
        self.config_file = "audio_config.ini"
        self.history_file = "audio_history.json"
        self.history_directory = os.path.expanduser("~/Documents/Audio Recordings")
        
        self.config = configparser.ConfigParser()
        self.load_config()
        
        self.chat_history = []
        self.load_history()

        self.status_callback = status_callback
        self.result_callback = result_callback
        self.transcript_callback = transcript_callback
        self.level_callback = level_callback
        self.summary_callback = None  # Set by API server for live summary streaming
        self._state_lock = threading.Lock()  # Protects live_transcript_text and live_insights
        self.live_transcript_text = ""  # Accumulated transcript for live summary
        self.live_insights = {           # Running insights state
            "meeting_type": None,
            "confidence": 0,
            "key_points": [],
            "action_items": [],
            "decisions": [],
            "sentiment": "neutral",
            "suggested_questions": [],
            "topic": ""
        }


        # Meeting Coach state (protected by self._state_lock)
        self.meeting_context = {
            "agenda": [],
            "notes": "",
            "expected_duration_minutes": None,
            "company_context": []
        }
        self.coach_alerts = []
        self.coach_callback = None  # Called when new alerts arrive (UI updates)
        self._coach_enabled = False

        # Resolve ffmpeg to absolute path once (prevents PATH manipulation attacks)
        self._ffmpeg_path = shutil.which('ffmpeg')
        if not self._ffmpeg_path:
            logger.warning("ffmpeg not found in PATH — live transcription will be unavailable")
        else:
            logger.info(f"ffmpeg resolved to: {self._ffmpeg_path}")

        self.detect_devices()

        # Preload model with slight delay to ensure UI loop is ready if it relies on callbacks immediately
        threading.Timer(1.0, self._preload_model).start()

    def set_mode(self, mode_str):
        mode_map = {"Microphone": "microphone", "System Audio": "system", "Hybrid": "hybrid"}
        self.recording_mode = mode_map.get(mode_str, "microphone")
        logger.info(f"Recording mode set to: {self.recording_mode}")

    def _preload_model(self):
        if not self.whisper_model and not self.model_loading:
            self.model_loading = True
            logger.info("Preloading Whisper model...")
            self.update_status("Loading AI Model...")
            try:
                self.whisper_model = whisper.load_model("base")
                logger.info("Whisper model loaded.")
                self.update_status("Ready")
            except Exception as e:
                logger.error(f"Failed to load Whisper: {e}")
                self.update_status("Model Error")
            finally:
                self.model_loading = False
                self.update_status("Ready")

    def update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def _get_api_key(self, provider: str) -> str:
        """Get an API key, preferring keychain over config file.

        Strips quotes that users sometimes add manually in config files.
        """
        # Try keychain first
        key = secure_store.get_api_key(provider)
        if key:
            return key.strip()

        # Fall back to config file
        raw_key = self.config['API_KEYS'].get(provider, '')
        return raw_key.strip().replace('"', '').replace("'", "")

    def _migrate_keys_to_keychain(self):
        """One-time migration: move API keys from plaintext config to keychain.

        After migration, removes keys from the INI file and rewrites it.
        """
        if not secure_store.is_available:
            return

        migrated_any = False
        for provider in ('openai', 'anthropic', 'gemini'):
            raw_key = self.config['API_KEYS'].get(provider, '')
            key = raw_key.strip().replace('"', '').replace("'", "")
            if key and not secure_store.get_api_key(provider):
                if secure_store.set_api_key(provider, key):
                    self.config.set('API_KEYS', provider, '')
                    migrated_any = True
                    logger.info(f"Migrated {provider} API key to keychain")

        if migrated_any:
            try:
                with open(self.config_file, 'w') as f:
                    self.config.write(f)
                logger.info("Cleared migrated keys from config file")
            except Exception as e:
                logger.error(f"Failed to rewrite config after migration: {e}")

    def load_config(self):
        self.config['API_KEYS'] = {'openai': '', 'anthropic': '', 'gemini': ''}
        self.config['SETTINGS'] = {
            'history_directory': self.history_directory,
            'default_llm': 'auto',
            'ollama_model': 'llama3:8b',
            'openai_model': 'gpt-4o',
            'anthropic_model': 'claude-sonnet-4-20250514'
        }
        self.config['COACH'] = {
            'enabled': 'true',
            'feed_urls': '',
            'feed_refresh_hours': '4',
            'coach_interval': '30'
        }
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)

                # Validate history_directory — must be under user's home
                raw_dir = self.config['SETTINGS'].get('history_directory', self.history_directory)
                resolved = os.path.realpath(os.path.expanduser(raw_dir))
                home = os.path.expanduser("~")
                if resolved.startswith(home):
                    self.history_directory = resolved
                else:
                    logger.warning(
                        "history_directory '%s' is outside home directory, "
                        "falling back to default", raw_dir
                    )
                    self.history_directory = os.path.expanduser("~/Documents/Audio Recordings")

            # Migrate plaintext keys to keychain (one-time, idempotent)
            self._migrate_keys_to_keychain()

            self.auto_detect_llm()
        except Exception as e:
            logger.error(f"Config warning: {e}")

    def auto_detect_llm(self):
        llm_priority = ['openai', 'gemini', 'anthropic', 'ollama']
        current_default = self.config['SETTINGS'].get('default_llm', 'auto')
        if current_default != 'auto': return

        for llm in llm_priority:
            if llm == 'ollama':
                self.config['SETTINGS']['default_llm'] = 'ollama'; break
            elif self._get_api_key(llm):
                self.config['SETTINGS']['default_llm'] = llm; break

    def detect_devices(self):
        try:
            # 1. Get Host API info (CoreAudio usually)
            host_apis = sd.query_hostapis()
            logger.info(f"Host APIs: {host_apis}")
            
            # 2. Iterate devices
            devices = sd.query_devices()
            
            default_input_idx = sd.default.device[0]
            
            for idx, info in enumerate(devices):
                if info['max_input_channels'] > 0:
                    name = info['name'].lower()
                    
                    # Store as valid sounddevice ID (int)
                    dev_data = {'index': idx, 'name': info['name'], 'channels': info['max_input_channels']}
                    
                    if idx == default_input_idx:
                        self.microphone_device = dev_data
                    
                    if 'blackhole' in name:
                        self.blackhole_device = dev_data
                    
                    if 'bbrew hybrid' in name:
                        self.hybrid_device = dev_data

            # Fallback if default not set somehow
            if not self.microphone_device and len(devices) > 0:
                 self.microphone_device = {'index': 0, 'name': devices[0]['name'], 'channels': devices[0]['max_input_channels']}

            logger.info(f"Devices detected: Mic={self.microphone_device}, Sys={self.blackhole_device}, Hybrid={self.hybrid_device}")
        except Exception as e:
            logger.error(f"Device detection error: {e}")

    def fetch_available_gemini_models(self):
        """Fetches available Gemini models using the Client pattern."""
        if not GOOGLE_GENAI_AVAILABLE: return []

        key = self._get_api_key('gemini')
        if not key: return []
        
        try:
            client = genai.Client(api_key=key)
            models = []
            for m in client.models.list():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name.replace('models/', ''))
            models.sort(reverse=True) # Prefer newer models (usually higher version numbers)
            logger.info(f"Discovered Gemini models: {models}")
            return models
        except Exception as e:
            logger.error(f"Model discovery error: {e}")
            return []

    def check_mic_permission(self):
        """
        Checks if microphone access is granted.
        This is a placeholder and might require OS-specific implementations.
        """
        # On macOS, if permission is not granted, pyaudio.PyAudio().open() will raise an OSError.
        # We'll rely on that error handling in record_audio for now.
        return True 

    def start_recording(self):
        if self.is_recording: return
        
        # PREVENT GIL STARVATION
        if self.model_loading:
            self.update_status("⚠️ AI Loading - Please Wait")
            logger.warning("User tried to start recording while model is loading.")
            return

        # RE-DETECT DEVICES (Handle plug/unplug)
        self.detect_devices()

        # PERMISSION CHECK
        if not self.check_mic_permission():
            logger.warning("Start recording aborted due to permissions.")
            return

        # DEVICE CHECK BASED ON MODE
        if self.recording_mode == 'system' and not self.blackhole_device:
            self.update_status("⚠️ BlackHole Not Found")
            logger.error("System audio requested but BlackHole not found.")
            return
            
        if self.recording_mode == 'hybrid' and not self.hybrid_device:
            self.update_status("⚠️ BBrew Hybrid Not Found")
            logger.error("Hybrid mode requested but 'BBrew Hybrid' device not found.")
            # Helper: Open Audio MIDI Setup
            try:
                subprocess.run(['/usr/bin/open', '-a', 'Audio MIDI Setup'])
            except Exception as e:
                logger.error(f"Failed to open Audio MIDI Setup: {e}")
            return

        self.is_recording = True

        with self._state_lock:
            self.live_transcript_text = ""  # Reset live transcript accumulator
        
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
        
        self.transcription_thread = threading.Thread(target=self.live_transcribe_loop)
        self.transcription_thread.start()
        
        self.summary_thread = threading.Thread(target=self.live_summary_loop)
        self.summary_thread.start()

        # Start coach thread if enabled
        self.coach_thread = None
        if self._coach_enabled:
            self.coach_thread = threading.Thread(target=self.live_coach_loop)
            self.coach_thread.start()

        self.recording_start_time = datetime.now()
        self.update_status("● Initializing...")
        logger.info("Recording started.")

    def stop_recording(self):
        # Guard against multiple calls (e.g. double-click stop button)
        if self._processing_audio:
            logger.warning("stop_recording() called but already processing - ignoring")
            return

        logger.info("Stopping recording...")
        self.is_recording = False
        self._processing_audio = True
        self.update_status("Processing final audio...")
        threading.Thread(target=self._async_stop_and_process).start()

    def _async_stop_and_process(self):
        try:
            logger.info("Waiting for threads to finish...")
            if self.recording_thread:
                self.recording_thread.join(timeout=3.0)
            if self.transcription_thread:
                self.transcription_thread.join(timeout=3.0)
            if hasattr(self, 'summary_thread') and self.summary_thread:
                self.summary_thread.join(timeout=3.0)
            if hasattr(self, 'coach_thread') and self.coach_thread:
                self.coach_thread.join(timeout=3.0)
            # Clean up coach state after threads are done
            self._coach_enabled = False
            self.process_audio()
        finally:
            self._processing_audio = False

    def record_audio(self):
        SAMPLE_RATE = 16000 # Whisper prefers 16k

        # Use mkstemp for unpredictable filenames (prevents symlink attacks)
        fd, self.temp_audio_file = tempfile.mkstemp(suffix='.wav', prefix='notsure_rec_')
        os.close(fd)  # We'll reopen with wave module
        self.part_file = self.temp_audio_file + '.part'
        logger.info(f"Writing audio to {self.part_file} (atomic)")
        
        q = queue.Queue()

        def audio_callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                logger.warning(f"Audio Callback Status: {status}")
            
            # RMS Calculation for VU Meter
            if self.level_callback:
                try:
                    data_float = indata.astype(float)
                    rms = np.sqrt(np.mean(data_float**2))
                    # Normalize: int16 max is 32768
                    norm_level = min(rms / 32768.0, 1.0)
                    self.level_callback(norm_level)
                except Exception: pass

            q.put(indata.copy())

        try:
            device = None
            if self.recording_mode == 'hybrid': device = self.hybrid_device
            elif self.recording_mode == 'system': device = self.blackhole_device
            else: device = self.microphone_device
            
            device_index = device['index'] if device else None
            
            with sd.InputStream(samplerate=SAMPLE_RATE, device=device_index,
                                channels=1, callback=audio_callback, dtype='int16'):
                
                self.update_status("● Recording...")
                success = False
                with wave.open(self.part_file, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2) # 16-bit
                    wf.setframerate(SAMPLE_RATE)
                    
                    while self.is_recording:
                        try:
                            # Non-blocking check for stop
                            data = q.get(timeout=1.0) 
                            wf.writeframes(data)
                            success = True
                        except queue.Empty:
                            # Keep loop alive if just quiet, or check if recording stopped
                            pass
                        except Exception as e:
                            logger.error(f"Write error: {e}")
                            break
            
            # Atomically rename part file — no exists() check to avoid TOCTOU race
            try:
                os.rename(self.part_file, self.temp_audio_file)
                logger.info(f"Renamed .part to {self.temp_audio_file} (success={success})")
            except FileNotFoundError:
                logger.warning(f"Part file does not exist: {self.part_file}")
            except OSError as rename_err:
                logger.error(f"Failed to rename .part file: {rename_err}")
                # Fallback: try to copy instead
                try:
                    shutil.copy2(self.part_file, self.temp_audio_file)
                    os.remove(self.part_file)
                    logger.info(f"Fallback: copied .part to {self.temp_audio_file}")
                except Exception as copy_err:
                    logger.error(f"Fallback copy also failed: {copy_err}")

        except Exception as e:
            logger.error(f"Recording error: {e}")
            logger.error(traceback.format_exc())
            self.update_status("Error: Recording Failed")
            self.is_recording = False
        finally:
            logger.info(f"Audio capture finished. File exists: {os.path.exists(self.temp_audio_file) if self.temp_audio_file else 'N/A'}")

    def live_transcribe_loop(self):
        logger.info("Live transcription loop started.")
        transcribe_count = 0

        while self.is_recording:
            time.sleep(3)  # Update every 3 seconds

            # Check prerequisites
            if not self.whisper_model:
                logger.debug("Live transcribe: Whisper model not loaded yet")
                if self.transcript_callback:
                    self.transcript_callback("Loading speech recognition model...")
                continue

            if not self.part_file or not os.path.exists(self.part_file):
                logger.debug(f"Live transcribe: Part file not ready (part_file={self.part_file})")
                continue

            # Check file size - need enough audio data
            try:
                file_size = os.path.getsize(self.part_file)
                if file_size < 8000:  # Less than ~0.25 seconds of audio
                    logger.debug(f"Live transcribe: File too small ({file_size} bytes)")
                    continue
            except Exception:
                continue

            # File grows, but header says 0 frames. Whisper needs valid header.
            # Use FFmpeg to copy/repair the stream to a temp file.
            try:
                if not self._ffmpeg_path:
                    logger.debug("Live transcribe: ffmpeg not available, skipping")
                    break

                temp_read_file = self.part_file + ".read.wav"

                # Fast copy with header update using ffmpeg (absolute path)
                result = subprocess.run(
                    [self._ffmpeg_path, '-y', '-i', self.part_file, '-c', 'copy', temp_read_file],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10
                )

                if result.returncode != 0 or not os.path.exists(temp_read_file):
                    logger.debug("Live transcribe: FFmpeg failed to create temp file")
                    continue

                transcribe_result = self.whisper_model.transcribe(temp_read_file, fp16=False)
                text = transcribe_result.get('text', '').strip()

                transcribe_count += 1
                logger.debug(f"Live transcribe #{transcribe_count}: {len(text)} chars")

                if text and self.transcript_callback:
                    self.transcript_callback(text)
                    with self._state_lock:
                        self.live_transcript_text = text  # Update accumulated transcript
                elif not text and self.transcript_callback:
                    self.transcript_callback("(Listening... no speech detected yet)")

                try:
                    os.remove(temp_read_file)
                except Exception:
                    pass

            except subprocess.TimeoutExpired:
                logger.warning("Live transcribe: FFmpeg timed out")
            except Exception as e:
                logger.debug(f"Live transcribe error (will retry): {e}")

        logger.info(f"Live transcription loop ended. Total transcriptions: {transcribe_count}")

    def _call_llm_json(self, prompt, llm=None):
        """Send a prompt to the configured LLM and return parsed JSON dict.

        Returns (data, meta) where data is the parsed dict (or None on failure)
        and meta is a dict with optional info like {'elapsed': float, 'error': str}.
        """
        if llm is None:
            llm = self.config['SETTINGS'].get('default_llm', 'ollama')
        meta = {}

        if llm == 'gemini':
            if not GOOGLE_GENAI_AVAILABLE:
                return None, {"error": "gemini_unavailable"}
            key = self._get_api_key('gemini')
            if not key:
                return None, {"error": "gemini_no_key"}
            try:
                client = genai.Client(api_key=key)
                selected_model = self.config['SETTINGS'].get('gemini_model', 'gemini-2.0-flash-exp')
                response = client.models.generate_content(
                    model=selected_model,
                    contents=[prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                text = response.text.strip()
                if text.startswith("```json"): text = text[7:-3]
                if text.startswith("```"): text = text[3:-3]
                return json.loads(text), meta
            except json.JSONDecodeError as e:
                logger.warning(f"_call_llm_json: Gemini JSON parse error: {e}")
                return None, {"error": "json_parse"}
            except Exception as e:
                logger.debug(f"_call_llm_json: Gemini error: {e}")
                return None, {"error": str(e)}

        elif llm == 'ollama':
            model = self.config['SETTINGS'].get('ollama_model', 'llama3:8b')
            try:
                start_t = time.time()
                resp = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": model, "stream": False, "prompt": prompt, "format": "json"},
                    timeout=90,
                )
                elapsed_t = time.time() - start_t
                meta["elapsed"] = elapsed_t
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
                if text.startswith("```json"): text = text[7:-3]
                if text.startswith("```"): text = text[3:-3]
                return json.loads(text), meta
            except requests.exceptions.ConnectionError:
                return None, {"error": "ollama_not_running"}
            except json.JSONDecodeError as e:
                logger.warning(f"_call_llm_json: Ollama JSON parse error: {e}")
                return None, {"error": "json_parse"}
            except Exception as e:
                logger.debug(f"_call_llm_json: Ollama error: {e}")
                return None, {"error": str(e)}

        elif llm == 'openai':
            if not OPENAI_AVAILABLE:
                return None, {"error": "openai_unavailable"}
            key = self._get_api_key('openai')
            if not key:
                return None, {"error": "openai_no_key"}
            try:
                model = self.config['SETTINGS'].get('openai_model', 'gpt-4o')
                client = openai.OpenAI(api_key=key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                text = response.choices[0].message.content.strip()
                if text.startswith("```json"): text = text[7:-3]
                if text.startswith("```"): text = text[3:-3]
                text = text.strip()
                return json.loads(text), meta
            except json.JSONDecodeError as e:
                logger.warning(f"_call_llm_json: OpenAI JSON parse error: {e}")
                return None, {"error": "json_parse"}
            except Exception as e:
                logger.debug(f"_call_llm_json: OpenAI error: {e}")
                return None, {"error": str(e)}

        elif llm == 'anthropic':
            if not ANTHROPIC_AVAILABLE:
                return None, {"error": "anthropic_unavailable"}
            key = self._get_api_key('anthropic')
            if not key:
                return None, {"error": "anthropic_no_key"}
            try:
                model = self.config['SETTINGS'].get('anthropic_model', 'claude-sonnet-4-20250514')
                client = anthropic.Anthropic(api_key=key)
                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text.strip()
                if text.startswith("```json"): text = text[7:-3]
                if text.startswith("```"): text = text[3:-3]
                text = text.strip()
                return json.loads(text), meta
            except json.JSONDecodeError as e:
                logger.warning(f"_call_llm_json: Anthropic JSON parse error: {e}")
                return None, {"error": "json_parse"}
            except Exception as e:
                logger.debug(f"_call_llm_json: Anthropic error: {e}")
                return None, {"error": str(e)}

        else:
            return None, {"error": f"unsupported_provider_{llm}"}

    def live_summary_loop(self):
        """Real-time conversation intelligence via Gemini or Ollama.

        Detects meeting type, extracts action items, decisions, sentiment,
        and suggests contextual follow-up questions periodically.
        """
        llm = self.config['SETTINGS'].get('default_llm', 'ollama')
        logger.info(f"Live insights loop started (provider: {llm}).")
        summary_count = 0
        ollama_disabled = False  # auto-disable if Ollama is too slow

        # Reset insights for this recording session
        with self._state_lock:
            self.live_insights = {
                "meeting_type": None,
                "confidence": 0,
                "key_points": [],
                "action_items": [],
                "decisions": [],
                "sentiment": "neutral",
                "suggested_questions": [],
                "topic": ""
            }

        # Determine interval: Ollama is slower, give it more time
        interval = 60 if llm == 'ollama' else 30

        # Don't start until we have a reasonable amount of transcript
        time.sleep(interval)

        while self.is_recording:
            # Only proceed if we have transcript text
            with self._state_lock:
                transcript_snapshot = self.live_transcript_text
            if not transcript_snapshot or len(transcript_snapshot.strip()) < 50:
                time.sleep(10)
                continue

            # Build the shared prompt (same for both providers)
            prev_context = ""
            if summary_count > 0:
                with self._state_lock:
                    insights_snapshot = dict(self.live_insights)
                prev_context = f"""\nPREVIOUS INSIGHTS (build on these, don't repeat):
- Meeting type: {insights_snapshot.get('meeting_type', 'unknown')}
- Topic: {insights_snapshot.get('topic', 'unknown')}
- Action items so far: {json.dumps(insights_snapshot.get('action_items', []))}
- Decisions so far: {json.dumps(insights_snapshot.get('decisions', []))}
"""

            prompt = f"""You are a real-time meeting analyst. Analyze this live conversation transcript and return structured insights.

Rules:
- meeting_type: classify as one of: standup, one_on_one, brainstorm, interview, all_hands, presentation, planning, retrospective, client_call, casual, other
- confidence: 0.0 to 1.0 for meeting_type classification
- key_points: 3-5 most important points discussed so far (concise bullet style)
- action_items: things someone committed to do, with "text" and "assignee" (use speaker label if available, else null)
- decisions: concrete decisions that were made (strings)
- sentiment: overall tone — one of: productive, tense, casual, confused, energetic, neutral
- suggested_questions: 1-2 contextual questions relevant to this meeting type that could move the conversation forward
- topic: concise main topic/subject of the meeting

Return ONLY a JSON object with these exact keys. For action_items, each item is {{"text": "...", "assignee": "..." or null}}.
Include ALL action items and decisions from previous insights plus any new ones (deduplicated).
{prev_context}
TRANSCRIPT (latest):
{transcript_snapshot[-3000:]}"""

            data = None

            if llm == 'ollama' and ollama_disabled:
                break

            data, meta = self._call_llm_json(prompt, llm)

            # Handle fatal errors that mean we should stop the loop
            if meta.get("error") in ("gemini_unavailable", "gemini_no_key",
                                      "ollama_not_running", "openai_unavailable",
                                      "openai_no_key", "anthropic_unavailable",
                                      "anthropic_no_key"):
                logger.info(f"Live insights: stopping due to {meta['error']}")
                break
            if meta.get("error", "").startswith("unsupported_provider"):
                logger.info(f"Live insights: provider '{llm}' not supported.")
                break

            # Auto-disable Ollama if too slow
            if llm == 'ollama' and meta.get("elapsed", 0) > 45:
                logger.warning(f"Live insights: Ollama took {meta['elapsed']:.0f}s — disabling.")
                ollama_disabled = True

            if data:
                summary_count += 1
                with self._state_lock:
                    self.live_insights.update(data)

                mt = data.get('meeting_type', '?')
                n_actions = len(data.get('action_items', []))
                n_decisions = len(data.get('decisions', []))
                logger.info(
                    f"Live insights #{summary_count}: type={mt}, "
                    f"actions={n_actions}, decisions={n_decisions}, "
                    f"sentiment={data.get('sentiment', '?')}"
                )

                if self.summary_callback:
                    self.summary_callback(data)

            # Wait between insight updates
            for _ in range(interval):
                if not self.is_recording:
                    break
                time.sleep(1)

        logger.info(f"Live insights loop ended. Total updates: {summary_count}")

    def get_live_insights(self):
        """Thread-safe read of live_insights."""
        with self._state_lock:
            return dict(self.live_insights)

    # --- Meeting Coach Methods ---

    def set_meeting_context(self, agenda_items, notes, duration_minutes=None):
        """Set meeting context before recording starts."""
        with self._state_lock:
            self.meeting_context = {
                "agenda": [{"text": item, "covered": False, "time_mentioned": None} for item in agenda_items],
                "notes": notes,
                "expected_duration_minutes": duration_minutes,
                "company_context": self._get_cached_feed_context()
            }
            self.coach_alerts = []

    def set_coach_enabled(self, enabled):
        """Enable or disable the meeting coach."""
        self._coach_enabled = enabled

    def get_coach_alerts(self):
        """Thread-safe read of coach_alerts."""
        with self._state_lock:
            return list(self.coach_alerts)

    def _get_cached_feed_context(self):
        """Get feed context strings, refreshing cache if stale."""
        try:
            from feed_fetcher import FeedFetcher
            if not hasattr(self, 'feed_fetcher'):
                self.feed_fetcher = FeedFetcher(config=self.config)
            urls_str = self.config.get('COACH', 'feed_urls', fallback='')
            urls = [u.strip() for u in urls_str.split(',') if u.strip()]
            if urls:
                self.feed_fetcher.refresh_if_needed(urls)
            return self.feed_fetcher.get_context_strings()
        except Exception as e:
            logger.debug(f"Feed context unavailable: {e}")
            return []

    def _build_coach_prompt(self, transcript, context, existing_alerts):
        """Build the LLM prompt for the meeting coach."""
        agenda_text = "\n".join([
            f"- {'[COVERED]' if item['covered'] else '[NOT YET]'} {item['text']}"
            for item in context.get("agenda", [])
        ]) or "(No agenda provided)"

        notes_text = context.get("notes", "").strip() or "(No notes provided)"

        company_ctx = "\n".join(context.get("company_context", [])) or "(No company context)"

        existing_summary = "\n".join([
            f"- [{a.get('timestamp', '??:??')}] {a.get('type', 'unknown')}: {a.get('message', '')}"
            for a in existing_alerts[-5:]
        ]) or "(No previous alerts)"

        return f"""You are a real-time meeting coach. Your job is to help the meeting participant stay on track and surface relevant information.

MEETING AGENDA:
{agenda_text}

PRE-MEETING NOTES:
{notes_text}

COMPANY CONTEXT (recent news/updates):
{company_ctx}

PREVIOUS ALERTS (do not repeat these):
{existing_summary}

CURRENT TRANSCRIPT (latest):
{transcript[-3000:]}

Analyze the conversation and return a JSON object:
{{
    "alerts": [
        {{
            "type": "off_topic|agenda_covered|agenda_missing|suggestion|context_ref|time_warning",
            "severity": "info|warning|critical",
            "message": "Short actionable message (1-2 sentences)",
            "agenda_item": "which agenda item this relates to, or null"
        }}
    ],
    "agenda_status": [
        {{
            "text": "exact text of agenda item",
            "covered": true
        }}
    ]
}}

Rules:
- Only generate NEW alerts not already in "PREVIOUS ALERTS"
- "off_topic": conversation strayed significantly from all agenda items
- "agenda_covered": an agenda item was adequately discussed (severity: info)
- "agenda_missing": meeting is progressing but a key agenda item hasn't been touched (severity: warning)
- "suggestion": a helpful question or redirect to bring conversation back on track
- "context_ref": something said connects to or contradicts company context (cite it)
- Keep alerts concise and actionable
- Return empty alerts array if nothing noteworthy happened since last check
- For agenda_status, only include items whose coverage status changed"""

    def _check_time_warnings(self):
        """Generate time-based alerts without needing LLM."""
        with self._state_lock:
            expected = self.meeting_context.get("expected_duration_minutes")
        if not expected or not self.recording_start_time:
            return

        elapsed_minutes = (datetime.now() - self.recording_start_time).total_seconds() / 60

        thresholds = [
            (0.75, "info", f"75% of planned time used ({int(elapsed_minutes)}m / {expected}m)"),
            (0.90, "warning", f"90% of planned time used ({int(elapsed_minutes)}m / {expected}m). Consider wrapping up."),
            (1.00, "critical", f"Meeting has exceeded planned duration of {expected}m."),
        ]

        for pct, severity, msg in thresholds:
            if elapsed_minutes >= expected * pct:
                alert_key = f"time_{int(pct * 100)}"
                with self._state_lock:
                    already_fired = any(a.get("id", "").startswith(alert_key) for a in self.coach_alerts)
                if not already_fired:
                    m, s = divmod(int(elapsed_minutes * 60), 60)
                    alert = {
                        "id": alert_key,
                        "timestamp": f"{m:02d}:{s:02d}",
                        "type": "time_warning",
                        "severity": severity,
                        "message": msg,
                        "agenda_item": None,
                        "source": "coach"
                    }
                    with self._state_lock:
                        self.coach_alerts.append(alert)
                    if self.coach_callback:
                        with self._state_lock:
                            alerts_copy = list(self.coach_alerts)
                            agenda_copy = list(self.meeting_context.get("agenda", []))
                        self.coach_callback(alerts_copy, agenda_copy)

    def live_coach_loop(self):
        """Real-time meeting coaching: off-topic detection, agenda tracking, time warnings."""
        llm = self.config['SETTINGS'].get('default_llm', 'ollama')
        logger.info(f"Live coach loop started (provider: {llm}).")
        coach_count = 0

        try:
            interval = int(self.config.get('COACH', 'coach_interval', fallback='30'))
        except (ValueError, configparser.Error):
            interval = 30

        # Wait before first analysis
        time.sleep(interval)

        while self.is_recording:
            with self._state_lock:
                transcript_snapshot = self.live_transcript_text
                context_snapshot = {
                    "agenda": [dict(item) for item in self.meeting_context.get("agenda", [])],
                    "notes": self.meeting_context.get("notes", ""),
                    "expected_duration_minutes": self.meeting_context.get("expected_duration_minutes"),
                    "company_context": list(self.meeting_context.get("company_context", []))
                }
                existing_alerts = list(self.coach_alerts)

            if not transcript_snapshot or len(transcript_snapshot.strip()) < 50:
                time.sleep(10)
                continue

            prompt = self._build_coach_prompt(transcript_snapshot, context_snapshot, existing_alerts)
            data, meta = self._call_llm_json(prompt, llm)

            # If provider is fatally unavailable, stop the loop
            if meta.get("error") in ("gemini_unavailable", "gemini_no_key",
                                      "ollama_not_running", "openai_unavailable",
                                      "openai_no_key", "anthropic_unavailable",
                                      "anthropic_no_key"):
                logger.info(f"Live coach: stopping due to {meta['error']}")
                break
            if meta.get("error", "").startswith("unsupported_provider"):
                logger.info(f"Live coach: provider '{llm}' not supported.")
                break

            if data:
                coach_count += 1
                new_alerts = data.get("alerts", [])
                agenda_updates = data.get("agenda_status", [])

                with self._state_lock:
                    # Append new alerts
                    for alert in new_alerts:
                        alert["id"] = uuid.uuid4().hex[:8]
                        alert["source"] = "coach"
                        if self.recording_start_time:
                            elapsed = (datetime.now() - self.recording_start_time).total_seconds()
                            m, s = divmod(int(elapsed), 60)
                            alert["timestamp"] = f"{m:02d}:{s:02d}"
                        self.coach_alerts.append(alert)

                    # Update agenda coverage
                    for status in agenda_updates:
                        for item in self.meeting_context.get("agenda", []):
                            if item["text"] == status.get("text") and status.get("covered"):
                                if not item["covered"]:
                                    item["covered"] = True
                                    if self.recording_start_time:
                                        elapsed = (datetime.now() - self.recording_start_time).total_seconds()
                                        m, s = divmod(int(elapsed), 60)
                                        item["time_mentioned"] = f"{m:02d}:{s:02d}"

                # Fire callback for UI
                if self.coach_callback:
                    with self._state_lock:
                        alerts_copy = list(self.coach_alerts)
                        agenda_copy = list(self.meeting_context.get("agenda", []))
                    self.coach_callback(alerts_copy, agenda_copy)

                logger.info(f"Coach #{coach_count}: {len(new_alerts)} new alerts")

            # Check time-based warnings (no LLM needed)
            self._check_time_warnings()

            # Sleep in 1-second increments for responsiveness
            for _ in range(interval):
                if not self.is_recording:
                    break
                time.sleep(1)

        logger.info(f"Live coach loop ended. Total updates: {coach_count}")

    def process_audio(self):
        logger.info("Processing logic started.")
        logger.info(f"Expected audio file: {self.temp_audio_file}")

        # Check for audio file with detailed diagnostics
        if not self.temp_audio_file:
            logger.error("temp_audio_file is None")
            self.update_status("Error: No audio file path set")
            return

        if not os.path.exists(self.temp_audio_file):
            # Check if .part file still exists (rename didn't complete)
            if hasattr(self, 'part_file') and self.part_file and os.path.exists(self.part_file):
                logger.warning(f"Part file exists but final file doesn't. Attempting rename...")
                try:
                    os.rename(self.part_file, self.temp_audio_file)
                    logger.info("Late rename successful")
                except Exception as e:
                    logger.error(f"Late rename failed: {e}")
                    self.update_status("Error: Audio file not ready")
                    return
            else:
                logger.error(f"Audio file does not exist: {self.temp_audio_file}")
                logger.error(f"Part file exists: {hasattr(self, 'part_file') and self.part_file and os.path.exists(self.part_file)}")
                self.update_status("Error: No audio file")
                return

        self.recording_end_time = datetime.now()
        duration_str = "0s"
        if self.recording_start_time:
             delta = self.recording_end_time - self.recording_start_time
             total_seconds = int(delta.total_seconds())
             m, s = divmod(total_seconds, 60)
             duration_str = f"{m}m {s}s" if m > 0 else f"{s}s"

        self.update_status("Finalizing Transcript...")
        try:
            if not self.whisper_model: self.whisper_model = whisper.load_model("base")

            if os.path.getsize(self.temp_audio_file) < 4096:
                raise AudioCaptureError("File too small - Audio subsystem failure detected")

            result = self.whisper_model.transcribe(self.temp_audio_file, fp16=False)

            formatted_transcript = ""
            for segment in result['segments']:
                start = self._format_time(segment['start'])
                end = self._format_time(segment['end'])
                text = segment['text'].strip()
                formatted_transcript += f"[{start}-{end}] Speaker: {text}\n"

            if not formatted_transcript.strip():
                formatted_transcript = "(No speech detected in recording)"

            self.update_status("Generating AI Summary...")
            # Pass the audio file path for cloud processing
            summary_data = self.generate_summary(formatted_transcript, self.temp_audio_file)

            # Enrich with Metadata
            summary_data["start_time"] = self.recording_start_time.strftime("%I:%M %p") if self.recording_start_time else "?"
            summary_data["end_time"] = self.recording_end_time.strftime("%I:%M %p") if self.recording_end_time else "?"
            summary_data["duration"] = duration_str

            self.save_to_history(formatted_transcript, summary_data)
            if self.result_callback: self.result_callback(summary_data)
            self.update_status("Ready")
            logger.info("Processing complete.")
        except Exception as e:
            msg = f"Processing error: {str(e)}"
            self.update_status(msg)
            logger.error(f"{msg}\n{traceback.format_exc()}")
        finally:
            # Clean up temp files
            for f in [self.temp_audio_file, self.part_file]:
                try:
                    if f and os.path.exists(f):
                        os.remove(f)
                        logger.debug(f"Cleaned up temp file: {f}")
                except OSError:
                    pass
            # Also clean up any leftover .read.wav file
            if self.part_file:
                read_file = self.part_file + ".read.wav"
                try:
                    if os.path.exists(read_file):
                        os.remove(read_file)
                except OSError:
                    pass

    def _format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def generate_summary(self, transcript, audio_path=None):
        llm = self.config['SETTINGS'].get('default_llm', 'ollama')
        logger.info(f"Summarizing with {llm}")
        if llm == 'gemini':
            return self._summarize_with_gemini(transcript, audio_path)
        elif llm == 'ollama':
            return self._summarize_with_ollama(transcript, audio_path)
        elif llm == 'openai':
            return self._summarize_with_openai(transcript, audio_path)
        elif llm == 'anthropic':
            return self._summarize_with_anthropic(transcript, audio_path)
        else:
            return self.error_summary(f"Unsupported LLM: {llm}", transcript)

    def _safe_error_message(self, e: Exception) -> str:
        """Sanitize exception messages before surfacing to the UI.

        Logs the full error at ERROR level but returns a user-friendly message
        that doesn't leak internal paths, API details, or key fragments.
        """
        err_str = str(e).lower()
        if isinstance(e, requests.ConnectionError) or 'connection' in err_str:
            return "Could not connect to the AI service"
        if isinstance(e, requests.Timeout) or 'timeout' in err_str:
            return "AI service timed out"
        if 'api_key' in err_str or 'unauthorized' in err_str or '401' in err_str or 'forbidden' in err_str:
            return "API authentication failed — check your API key in Settings"
        if 'quota' in err_str or 'rate' in err_str or '429' in err_str:
            return "API rate limit or quota exceeded — try again later"
        # Generic fallback — real error logged, not shown to user
        logger.error(f"API error details: {e}", exc_info=True)
        return "An unexpected error occurred during AI processing"

    def _summarize_with_gemini(self, transcript, audio_path=None):
        if not GOOGLE_GENAI_AVAILABLE: return self.error_summary("Google GenAI Lib Missing", transcript)

        key = self._get_api_key('gemini')
        if not key: return self.error_summary("Gemini API Key Missing", transcript)

        logger.info("Sending request to Gemini API (V1 SDK)...")
        try:
            client = genai.Client(api_key=key)
            
            # Use selected model or fallback
            selected_model = self.config['SETTINGS'].get('gemini_model', 'gemini-2.0-flash-exp')
            reasoning_level = self.config['SETTINGS'].get('reasoning_level', 'Standard')
            
            logger.info(f"Generating content with model: {selected_model}, Reasoning: {reasoning_level}")
            
            # CONFIGURATION
            try:
                gen_config = types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
                
                if reasoning_level == "Deep Think":
                    gen_config.thinking_config = types.ThinkingConfig(include_thoughts=True)
                    
            except Exception as e:
                logger.warning(f"Failed to create Config: {e}")
                gen_config = None

            content_payload = []
            
            # 1. Attempt Audio Upload (Horizon 3: Cloud Diarization)
            file_uploaded = False
            if audio_path and os.path.exists(audio_path):
                try:
                    self.update_status("Uploading Audio to Cloud...")
                    logger.info(f"Uploading file: {audio_path}")
                    
                    # Upload (google-genai SDK uses 'file' parameter)
                    audio_file = client.files.upload(file=audio_path)
                    content_payload.append(audio_file)
                    content_payload.append("Analyze this recording. Identify speakers (Speaker A, B, etc.) if distinct.")
                    file_uploaded = True
                    logger.info(f"File ready: {audio_file.name}")
                    
                except Exception as e:
                    logger.error(f"Audio upload failed, backing due to text: {e}")
                    self.update_status("Cloud Upload Failed")
            
            # 2. Fallback or Supplement with Transcript
            if not file_uploaded:
                content_payload.append(f"TRANSCRIPT:\n{transcript}")

            prompt_str = """
            You are an expert executive assistant. Analyze the meeting.
            
            SPEAKER DIARIZATION:
            - Attempt to identify distinct speakers based on the audio (if provided) or text patterns.
            - Assign them labels like "Speaker 1", "Speaker A", or names if mentioned in conversation.
            - Estimate the total number of distinct speakers.
            - Produce a diarized_transcript: an array of objects, each with speaker, timestamp, and text.

            Output a JSON object with this EXACT structure:
            {
                "title": "Short title",
                "executive_summary": "High-level summary.",
                "speaker_info": {
                    "count": 2,
                    "list": ["Speaker 1", "Speaker 2"]
                },
                "diarized_transcript": [
                    {"speaker": "Speaker 1", "timestamp": "00:00-00:15", "text": "What they said"},
                    {"speaker": "Speaker 2", "timestamp": "00:15-00:30", "text": "Their response"}
                ],
                "highlights": ["Point 1", "Point 2"],
                "full_summary_sections": [{"header": "Topic", "content": "Details", "quote": "Quote", "attribution": "Speaker 1"}],
                "tasks": [{"description": "Task", "assignee": "Name", "due_date": "Date"}]
            }
            """
            content_payload.append(prompt_str)

            self.update_status("AI Thinking..." if reasoning_level=="Deep Think" else "AI Summarizing...")
            
            response = client.models.generate_content(
                model=selected_model,
                contents=content_payload,
                config=gen_config
            )
            logger.info("Received response from Gemini.")
            
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:-3]
            if text.startswith("```"): text = text[3:-3]

            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini summary JSON: {e}")
                return self.error_summary(f"Failed to parse AI response", transcript)
            data["date"] = datetime.now().strftime("%b %d at %I:%M %p")
            data["transcript"] = transcript
            
            # Build enhanced transcript from diarized data if available
            if "diarized_transcript" in data and isinstance(data["diarized_transcript"], list) and len(data["diarized_transcript"]) > 0:
                diarized_lines = []
                for seg in data["diarized_transcript"]:
                    speaker = seg.get("speaker", "Speaker")
                    ts = seg.get("timestamp", "")
                    txt = seg.get("text", "").strip()
                    if ts:
                        diarized_lines.append(f"[{ts}] {speaker}: {txt}")
                    else:
                        diarized_lines.append(f"{speaker}: {txt}")
                data["diarized_transcript_text"] = "\n".join(diarized_lines)
                logger.info(f"Diarized transcript: {len(data['diarized_transcript'])} segments, {len(data.get('speaker_info', {}).get('list', []))} speakers")
            
            return data
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return self.error_summary(f"Gemini Error: {self._safe_error_message(e)}", transcript)

    def error_summary(self, error_msg, transcript):
        return {"title": "Error Processing", "executive_summary": error_msg, "full_summary": "", "tasks": [], "transcript": transcript}

    def _summarize_with_ollama(self, transcript, audio_path=None):
        """Summarize transcript using local Ollama LLM with structured JSON output."""
        # Health check - verify Ollama is running
        try:
            health_response = requests.get("http://localhost:11434/api/tags", timeout=5)
            health_response.raise_for_status()
        except requests.exceptions.ConnectionError:
            return self.error_summary("Ollama not running. Start with: ollama serve", transcript)
        except requests.exceptions.Timeout:
            return self.error_summary("Ollama health check timed out", transcript)
        except Exception as e:
            return self.error_summary(f"Ollama connection error: {str(e)}", transcript)

        model = self.config['SETTINGS'].get('ollama_model', 'llama3:8b')
        logger.info(f"Sending request to Ollama (model: {model})...")
        self.update_status("AI Summarizing (Local)...")

        prompt = f"""You are an expert executive assistant. Analyze the following meeting transcript.

TRANSCRIPT:
{transcript}

Output a JSON object with this EXACT structure (no markdown, no explanation, ONLY the JSON object):
{{
    "title": "Short descriptive title for this meeting",
    "executive_summary": "2-3 sentence high-level summary of the meeting.",
    "speaker_info": {{
        "count": 2,
        "list": ["Speaker 1", "Speaker 2"]
    }},
    "diarized_transcript": [
        {{"speaker": "Speaker 1", "timestamp": "00:00-00:15", "text": "What they said"}},
        {{"speaker": "Speaker 2", "timestamp": "00:15-00:30", "text": "Their response"}}
    ],
    "highlights": ["Key point 1", "Key point 2", "Key point 3"],
    "full_summary_sections": [
        {{"header": "Topic", "content": "Details about this topic", "quote": "Relevant quote", "attribution": "Speaker 1"}}
    ],
    "tasks": [
        {{"description": "Action item description", "assignee": "Person name or null", "due_date": "Date or null"}}
    ]
}}

Rules:
- Identify distinct speakers from text patterns and label them.
- Extract ALL action items mentioned.
- Provide at least 3 highlights.
- If you cannot identify speakers, use "Speaker 1", "Speaker 2", etc.
- Return ONLY valid JSON. No markdown fences, no extra text."""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "stream": False,
                    "prompt": prompt,
                    "format": "json",
                },
                timeout=180,
            )
            response.raise_for_status()

            result = response.json()
            text = result.get("response", "").strip()
            logger.info(f"Ollama response length: {len(text)} chars")

            # Strip markdown fences if present
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            data["date"] = datetime.now().strftime("%b %d at %I:%M %p")
            data["transcript"] = transcript

            # Ensure required fields exist
            if "tasks" not in data: data["tasks"] = []
            if "highlights" not in data: data["highlights"] = []
            if "full_summary_sections" not in data: data["full_summary_sections"] = []

            # Build enhanced transcript from diarized data if available
            if "diarized_transcript" in data and isinstance(data["diarized_transcript"], list) and len(data["diarized_transcript"]) > 0:
                diarized_lines = []
                for seg in data["diarized_transcript"]:
                    speaker = seg.get("speaker", "Speaker")
                    ts = seg.get("timestamp", "")
                    txt = seg.get("text", "").strip()
                    if ts:
                        diarized_lines.append(f"[{ts}] {speaker}: {txt}")
                    else:
                        diarized_lines.append(f"{speaker}: {txt}")
                data["diarized_transcript_text"] = "\n".join(diarized_lines)
                logger.info(f"Ollama diarized transcript: {len(data['diarized_transcript'])} segments")

            logger.info(f"Ollama summary generated: {data.get('title', 'No title')}")
            return data

        except requests.exceptions.Timeout:
            msg = f"Ollama timed out after 180s (model: {model}). Try a smaller model."
            logger.error(msg)
            return self.error_summary(msg, transcript)
        except json.JSONDecodeError as e:
            logger.error(f"Ollama JSON parse error: {e}, response: {text[:500] if text else 'empty'}")
            # Try to salvage a basic summary from the raw text
            return {
                "title": f"Meeting {datetime.now().strftime('%b %d')}",
                "date": datetime.now().strftime("%b %d at %I:%M %p"),
                "executive_summary": text[:500] if text else "Ollama returned unparseable output.",
                "full_summary": text or "",
                "tasks": [],
                "transcript": transcript,
            }
        except Exception as e:
            logger.error(f"Ollama API error: {e}\n{traceback.format_exc()}")
            return self.error_summary(f"Ollama error: {self._safe_error_message(e)}", transcript)

    def _summarize_with_openai(self, transcript, audio_path=None):
        """Summarize transcript using OpenAI API."""
        if not OPENAI_AVAILABLE:
            return self.error_summary("OpenAI library not installed (pip install openai)", transcript)

        key = self._get_api_key('openai')
        if not key:
            return self.error_summary("OpenAI API Key Missing", transcript)

        model = self.config['SETTINGS'].get('openai_model', 'gpt-4o')
        logger.info(f"Using OpenAI model: {model}")

        prompt = """You are an expert executive assistant. Analyze the following meeting transcript and return a structured JSON summary.

Output ONLY a valid JSON object with this EXACT structure:
{
    "title": "Short descriptive title for the meeting",
    "executive_summary": "2-3 sentence high-level summary of what was discussed",
    "speaker_info": {
        "count": 1,
        "list": ["Speaker 1"]
    },
    "highlights": ["Key point 1", "Key point 2", "Key point 3"],
    "full_summary_sections": [
        {"header": "Main Topic", "content": "Details about this topic"}
    ],
    "tasks": [
        {"description": "Action item description", "assignee": "Person name or null", "due_date": "Date or null"}
    ]
}

TRANSCRIPT:
""" + transcript

        try:
            self.update_status("AI Summarizing (OpenAI)...")
            client = openai.OpenAI(api_key=key)

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response length: {len(text)} chars")

            # Handle potential markdown wrappers
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            data["date"] = datetime.now().strftime("%b %d at %I:%M %p")
            data["transcript"] = transcript

            if "tasks" not in data:
                data["tasks"] = []
            if "highlights" not in data:
                data["highlights"] = []
            if "full_summary_sections" not in data:
                data["full_summary_sections"] = []

            logger.info(f"OpenAI summary generated: {data.get('title', 'No title')}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"OpenAI JSON parse error: {e}")
            return self.error_summary("OpenAI returned invalid JSON", transcript)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self.error_summary(f"OpenAI error: {self._safe_error_message(e)}", transcript)

    def _summarize_with_anthropic(self, transcript, audio_path=None):
        """Summarize transcript using Anthropic API."""
        if not ANTHROPIC_AVAILABLE:
            return self.error_summary("Anthropic library not installed (pip install anthropic)", transcript)

        key = self._get_api_key('anthropic')
        if not key:
            return self.error_summary("Anthropic API Key Missing", transcript)

        model = self.config['SETTINGS'].get('anthropic_model', 'claude-sonnet-4-20250514')
        logger.info(f"Using Anthropic model: {model}")

        prompt = """You are an expert executive assistant. Analyze the following meeting transcript and return a structured JSON summary.

Output ONLY a valid JSON object with this EXACT structure (no markdown, no code blocks):
{
    "title": "Short descriptive title for the meeting",
    "executive_summary": "2-3 sentence high-level summary of what was discussed",
    "speaker_info": {
        "count": 1,
        "list": ["Speaker 1"]
    },
    "highlights": ["Key point 1", "Key point 2", "Key point 3"],
    "full_summary_sections": [
        {"header": "Main Topic", "content": "Details about this topic"}
    ],
    "tasks": [
        {"description": "Action item description", "assignee": "Person name or null", "due_date": "Date or null"}
    ]
}

TRANSCRIPT:
""" + transcript

        try:
            self.update_status("AI Summarizing (Anthropic)...")
            client = anthropic.Anthropic(api_key=key)

            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text.strip()
            logger.info(f"Anthropic response length: {len(text)} chars")

            # Handle potential markdown wrappers
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            data["date"] = datetime.now().strftime("%b %d at %I:%M %p")
            data["transcript"] = transcript

            if "tasks" not in data:
                data["tasks"] = []
            if "highlights" not in data:
                data["highlights"] = []
            if "full_summary_sections" not in data:
                data["full_summary_sections"] = []

            logger.info(f"Anthropic summary generated: {data.get('title', 'No title')}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Anthropic JSON parse error: {e}")
            return self.error_summary("Anthropic returned invalid JSON", transcript)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self.error_summary(f"Anthropic error: {self._safe_error_message(e)}", transcript)

    def save_to_history(self, transcript, summary_data):
        entry = summary_data if isinstance(summary_data, dict) else {"full_summary": str(summary_data)}
        if "transcript" not in entry: entry["transcript"] = transcript
        if "timestamp" not in entry: entry["timestamp"] = str(datetime.now())
        self.chat_history.insert(0, entry)
        try:
            with open(self.history_file, 'w') as f: json.dump(self.chat_history, f, indent=4)
        except Exception as e:
            logger.error(f"Save history error: {e}")

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f: self.chat_history = json.load(f)
            except Exception: self.chat_history = []

    # --- JOURNAL SUPPORT ---

    def __init_journal(self):
        """Initialize journal storage"""
        if not hasattr(self, 'journal_file'):
            self.journal_file = "journal_history.json"
            self.journal_entries = []
            self.load_journal()

    def load_journal(self):
        """Load journal entries from file"""
        self.__init_journal()
        if os.path.exists(self.journal_file):
            try:
                with open(self.journal_file, 'r') as f:
                    self.journal_entries = json.load(f)
            except Exception:
                self.journal_entries = []

    def save_journal(self):
        """Save journal entries to file"""
        self.__init_journal()
        try:
            with open(self.journal_file, 'w') as f:
                json.dump(self.journal_entries, f, indent=4)
        except Exception as e:
            logger.error(f"Save journal error: {e}")

    def create_journal_entry(self, entry_text: str) -> dict:
        """Create a new journal entry"""
        self.__init_journal()
        import uuid
        entry = {
            "id": str(uuid.uuid4()),
            "date": datetime.now().strftime("%b %d, %Y at %I:%M %p"),
            "timestamp": str(datetime.now()),
            "entry": entry_text,
            "ai_suggestions": ""
        }
        self.journal_entries.insert(0, entry)
        self.save_journal()
        return entry

    def get_journal_entries(self) -> list:
        """Get all journal entries"""
        self.__init_journal()
        return self.journal_entries

    def optimize_journal_entry(self, entry_id: str) -> str:
        """Generate AI suggestions for a journal entry"""
        self.__init_journal()

        # Find the entry
        entry = None
        for e in self.journal_entries:
            if e.get("id") == entry_id:
                entry = e
                break

        if not entry:
            return "Entry not found"

        entry_text = entry.get("entry", "")

        # Use Gemini to generate suggestions
        if not GOOGLE_GENAI_AVAILABLE:
            return "AI suggestions require Google GenAI library"

        key = self._get_api_key('gemini')
        if not key:
            return "Please configure your Gemini API key in settings"

        try:
            client = genai.Client(api_key=key)
            selected_model = self.config['SETTINGS'].get('gemini_model', 'gemini-2.0-flash-exp')

            prompt = f"""You are a thoughtful life coach and productivity assistant.
            Based on this journal entry, provide helpful suggestions, insights, or action items.
            Be supportive and constructive. Keep response concise (2-4 sentences).

            Journal entry: "{entry_text}"
            """

            response = client.models.generate_content(
                model=selected_model,
                contents=[prompt]
            )

            suggestions = response.text.strip()

            # Update the entry
            entry["ai_suggestions"] = suggestions
            self.save_journal()

            return suggestions

        except Exception as e:
            logger.error(f"Journal optimization error: {e}")
            return f"Error generating suggestions: {self._safe_error_message(e)}"

    # --- SESSION MANAGEMENT ---

    def __init_session(self):
        """Initialize session storage"""
        if not hasattr(self, 'session_file'):
            self.session_file = "session.json"
            self.session = {}
            self.load_session()

    def load_session(self):
        """Load session from file"""
        self.__init_session()
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    self.session = json.load(f)
            except Exception:
                self.session = {}

    def save_session(self):
        """Save session to file"""
        self.__init_session()
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.session, f, indent=4)
        except Exception as e:
            logger.error(f"Save session error: {e}")

    def login(self, provider: str, email: str = None) -> bool:
        """Log in a user"""
        self.__init_session()
        self.session = {
            "logged_in": True,
            "provider": provider,
            "email": email or f"user@{provider}.com",
            "login_time": str(datetime.now())
        }
        self.save_session()
        logger.info(f"User logged in via {provider}")
        return True

    def logout(self):
        """Log out the user"""
        self.__init_session()
        self.session = {"logged_in": False}
        self.save_session()
        logger.info("User logged out")

    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        self.__init_session()
        return self.session.get("logged_in", False)

    def get_user_info(self) -> dict:
        """Get current user info"""
        self.__init_session()
        return {
            "email": self.session.get("email", ""),
            "provider": self.session.get("provider", ""),
        }
