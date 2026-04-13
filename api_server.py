"""
FastAPI Server - Audio Summary App Backend API

This server exposes the Python backend (audio recording, transcription, summarization)
as REST and WebSocket endpoints for the React frontend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import os
import time
from datetime import datetime
import threading
import logging
import requests as http_requests  # renamed to avoid clash with FastAPI Request

# Import the existing backend
from backend import EnhancedAudioApp

# Secure credential storage
from secure_store import secure_store

logger = logging.getLogger(__name__)

# --- Lifespan must be defined before FastAPI() so it can be passed to the constructor ---

# Global state
backend_app = None
_event_loop = None
active_websockets = set()

async def broadcast_status(message: str):
    """Send status updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "status", "message": message})
        except Exception:
            pass

async def broadcast_transcript(text: str):
    """Send live transcript updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "transcript_update", "text": text})
        except Exception:
            pass

async def broadcast_level(level: float):
    """Send audio level updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "audio_level", "value": level})
        except Exception:
            pass

async def broadcast_live_summary(data: dict):
    """Send live summary updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "live_summary", "data": data})
        except Exception:
            pass

async def broadcast_completion():
    """Send recording-complete event to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "status", "status": "complete"})
        except Exception:
            pass

async def broadcast_error(error_message: str):
    """Send processing-error event to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "status", "status": "error", "error": error_message})
        except Exception:
            pass

def status_callback(message: str):
    if _event_loop:
        asyncio.run_coroutine_threadsafe(broadcast_status(message), _event_loop)

def transcript_callback(text: str):
    if _event_loop:
        asyncio.run_coroutine_threadsafe(broadcast_transcript(text), _event_loop)

def level_callback(level: float):
    if _event_loop:
        asyncio.run_coroutine_threadsafe(broadcast_level(level), _event_loop)

def live_summary_callback(data: dict):
    if _event_loop:
        asyncio.run_coroutine_threadsafe(broadcast_live_summary(data), _event_loop)

def result_callback(summary_data):
    if _event_loop:
        asyncio.run_coroutine_threadsafe(broadcast_completion(), _event_loop)

def error_callback(error_message: str):
    if _event_loop:
        asyncio.run_coroutine_threadsafe(broadcast_error(error_message), _event_loop)

@asynccontextmanager
async def lifespan(app):
    """Initialize the backend on server start"""
    global backend_app, _event_loop
    _event_loop = asyncio.get_running_loop()
    backend_app = EnhancedAudioApp()
    backend_app.status_callback = status_callback
    backend_app.result_callback = result_callback
    backend_app.error_callback = error_callback
    backend_app.transcript_callback = transcript_callback
    backend_app.level_callback = level_callback
    backend_app.summary_callback = live_summary_callback
    print("✓ Backend initialized")
    yield

app = FastAPI(
    title="Audio Summary API",
    description="Local API for audio recording, transcription, and AI summarization",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_duration_to_seconds(duration_val) -> int:
    """Convert duration string like '5m 23s' or '24s' or int to seconds."""
    if isinstance(duration_val, (int, float)):
        return int(duration_val)
    if not isinstance(duration_val, str):
        return 0
    import re
    total = 0
    hours = re.findall(r'(\d+)\s*h', duration_val)
    mins = re.findall(r'(\d+)\s*m', duration_val)
    secs = re.findall(r'(\d+)\s*s', duration_val)
    if hours: total += int(hours[0]) * 3600
    if mins: total += int(mins[0]) * 60
    if secs: total += int(secs[0])
    return total

# Pydantic models
class RecordingStartRequest(BaseModel):
    title: Optional[str] = None
    speakers: Optional[List[str]] = []
    device: Optional[str] = None

class RecordingStopResponse(BaseModel):
    success: bool
    meeting_id: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[dict] = None
    error: Optional[str] = None

class Meeting(BaseModel):
    id: str
    title: str
    date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[int] = None
    speakers: List[str] = []
    transcript: Optional[str] = None
    summary: Optional[dict] = None
    tags: List[str] = []

class Task(BaseModel):
    id: str
    meeting_id: str
    text: str
    assignee: Optional[str] = None
    completed: bool = False
    created_at: str

class Person(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    last_meeting: Optional[str] = None
    meeting_count: int = 0

class SettingsUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_model: Optional[str] = None
    llm_provider: Optional[str] = None
    launch_on_startup: Optional[bool] = None
    show_in_menubar: Optional[bool] = None
    dark_mode: Optional[bool] = None
    language: Optional[str] = None
    obsidian_enabled: Optional[bool] = None
    obsidian_vault_path: Optional[str] = None
    obsidian_folder: Optional[str] = None

class PermissionRequest(BaseModel):
    permission: str  # "microphone", "screen_recording", etc.


# Serve React frontend from figma-ui/dist (if available)
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figma-ui", "dist")
_FRONTEND_AVAILABLE = os.path.isdir(_FRONTEND_DIR) and os.path.isfile(os.path.join(_FRONTEND_DIR, "index.html"))

@app.get("/")
async def root():
    if _FRONTEND_AVAILABLE:
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))
    return {"status": "ok", "message": "Audio Summary API is running"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "backend_ready": backend_app is not None,
        "model_loaded": backend_app.whisper_model is not None if backend_app else False
    }

# ==================== PERMISSIONS ====================

@app.post("/api/permissions/open")
async def open_permission_settings(req: PermissionRequest):
    """Open the specific macOS System Settings pane for a permission."""
    import subprocess
    PERM_URLS = {
        "microphone": "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone",
        "screen_recording": "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        "accessibility": "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        "input_monitoring": "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
    }
    url = PERM_URLS.get(req.permission)
    if not url:
        raise HTTPException(status_code=400, detail=f"Unknown permission: {req.permission}")
    subprocess.Popen(["open", url])
    return {"success": True, "opened": req.permission}

@app.get("/api/permissions/status")
async def get_permission_status():
    """Check which macOS permissions are granted (proxy via device detection)."""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    backend_app.detect_devices()
    return {
        "microphone": backend_app.microphone_device is not None,
        "system_audio": backend_app.blackhole_device is not None,
        "screen_recording": False,
    }

# ==================== DEVICES ====================

@app.get("/api/devices")
async def get_devices():
    """Get available audio input devices"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    backend_app.detect_devices()
    return {
        "microphone": {"name": "Microphone", "available": backend_app.microphone_device is not None},
        "system_audio": {"name": "System Audio (BlackHole)", "available": backend_app.blackhole_device is not None},
        "hybrid": {"name": "Hybrid (BBrew)", "available": backend_app.hybrid_device is not None},
        "default": "microphone"
    }

# ==================== RECORDING ====================

@app.post("/api/recordings/start")
async def start_recording(request: RecordingStartRequest):
    """Start audio recording"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    if backend_app.is_recording:
        raise HTTPException(status_code=409, detail="Recording already in progress")

    # Apply device selection
    if request.device:
        device_map = {"microphone": "microphone", "system_audio": "system", "hybrid": "hybrid"}
        backend_app.recording_mode = device_map.get(request.device, "microphone")

    # Start recording in background thread
    threading.Thread(target=backend_app.start_recording, daemon=True).start()
    
    return {
        "success": True,
        "message": "Recording started",
        "title": request.title
    }

@app.post("/api/recordings/mute")
async def toggle_mute():
    """Toggle mute state on the recording"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    if not backend_app.is_recording:
        raise HTTPException(status_code=409, detail="No recording in progress")
    backend_app.is_muted = not backend_app.is_muted
    return {"success": True, "muted": backend_app.is_muted}

@app.post("/api/recordings/stop")
async def stop_recording():
    """Stop recording and process audio"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    if not backend_app.is_recording:
        raise HTTPException(status_code=409, detail="No recording in progress")
    
    # Stop recording
    backend_app.stop_recording()
    
    return {
        "success": True,
        "message": "Recording stopped, processing audio..."
    }

@app.get("/api/recordings/status")
async def recording_status():
    """Get current recording status with live meeting intelligence"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    duration = 0
    if backend_app.is_recording and backend_app.recording_start_time:
        from datetime import datetime as dt
        duration = int((dt.now() - backend_app.recording_start_time).total_seconds())
    
    insights = backend_app.get_live_insights() if hasattr(backend_app, 'get_live_insights') else {}
    return {
        "is_recording": backend_app.is_recording,
        "duration": duration,
        "meeting_type": insights.get("meeting_type"),
        "topic": insights.get("topic", ""),
        "sentiment": insights.get("sentiment", "neutral"),
    }


@app.get("/api/recordings/insights")
async def recording_insights():
    """Get full live insights snapshot (meeting type, action items, decisions, etc.)"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    if hasattr(backend_app, 'get_live_insights'):
        return backend_app.get_live_insights()
    return {
        "meeting_type": None,
        "confidence": 0,
        "key_points": [],
        "action_items": [],
        "decisions": [],
        "sentiment": "neutral",
        "suggested_questions": [],
        "topic": ""
    }

# ==================== MEETINGS ====================

@app.get("/api/meetings")
async def get_meetings():
    """Get all meetings from history"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    # Use chat_history attribute directly instead of load_history()
    history = backend_app.chat_history or []
    
    meetings = []
    for idx, entry in enumerate(history):
        if not isinstance(entry, dict):
            continue  # Skip malformed entries
        
        # Get speaker info - could be dict with 'list' key or direct list
        speaker_info = entry.get("speaker_info", {})
        speakers = []
        if isinstance(speaker_info, dict):
            speakers = speaker_info.get("list", [])
        elif isinstance(speaker_info, list):
            speakers = speaker_info
            
        meeting = {
            "id": str(idx),
            "title": entry.get("title", f"Meeting {idx + 1}"),
            "date": entry.get("timestamp", entry.get("date", "")),
            "duration": parse_duration_to_seconds(entry.get("duration", entry.get("duration_seconds", 0))),
            "speakers": speakers,
            "transcript": entry.get("transcript", ""),
            "executive_summary": entry.get("executive_summary", ""),
            "highlights": entry.get("highlights", []),
            "tasks": entry.get("tasks", []),
            "tags": entry.get("tags", []),
            "start_time": entry.get("start_time", ""),
            "end_time": entry.get("end_time", "")
        }
        meetings.append(meeting)
    
    return {"meetings": meetings}

# ==================== SEARCH ====================
# NOTE: This must be defined BEFORE /api/meetings/{meeting_id} to avoid
# FastAPI matching "search" as a meeting_id parameter.

@app.get("/api/meetings/search")
async def search_meetings(q: str = "", fields: str = "title,transcript,executive_summary,speakers"):
    """Full-text search across all meetings"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")

    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}

    query = q.strip().lower()
    search_fields = [f.strip() for f in fields.split(",")]
    history = backend_app.chat_history or []
    results = []

    for idx, entry in enumerate(history):
        if not isinstance(entry, dict):
            continue

        matches = []

        # Search in text fields
        for field in search_fields:
            value = ""
            if field == "speakers":
                speaker_info = entry.get("speaker_info", {})
                if isinstance(speaker_info, dict):
                    value = " ".join(speaker_info.get("list", []))
                elif isinstance(speaker_info, list):
                    value = " ".join(str(s) for s in speaker_info)
            elif field == "highlights":
                value = " ".join(entry.get("highlights", []))
            else:
                value = str(entry.get(field, ""))

            if query in value.lower():
                # Extract a snippet around the match
                lower_val = value.lower()
                match_pos = lower_val.find(query)
                start = max(0, match_pos - 60)
                end = min(len(value), match_pos + len(query) + 60)
                snippet = value[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(value):
                    snippet = snippet + "..."

                matches.append({
                    "field": field,
                    "snippet": snippet
                })

        if matches:
            # Get speaker info
            speaker_info = entry.get("speaker_info", {})
            speakers = []
            if isinstance(speaker_info, dict):
                speakers = speaker_info.get("list", [])
            elif isinstance(speaker_info, list):
                speakers = speaker_info

            results.append({
                "meeting_id": str(idx),
                "title": entry.get("title", f"Meeting {idx + 1}"),
                "date": entry.get("timestamp", entry.get("date", "")),
                "speakers": speakers,
                "matches": matches
            })

    return {"results": results, "query": q, "total": len(results)}

@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get a specific meeting by ID"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    history = backend_app.chat_history or []
    
    try:
        idx = int(meeting_id)
        if idx < 0 or idx >= len(history):
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        entry = history[idx]
        if not isinstance(entry, dict):
            raise HTTPException(status_code=404, detail="Meeting data corrupted")
        
        # Get speaker info
        speaker_info = entry.get("speaker_info", {})
        speakers = []
        if isinstance(speaker_info, dict):
            speakers = speaker_info.get("list", [])
        elif isinstance(speaker_info, list):
            speakers = speaker_info
            
        return {
            "id": meeting_id,
            "title": entry.get("title", f"Meeting {idx + 1}"),
            "date": entry.get("timestamp", entry.get("date", "")),
            "duration": parse_duration_to_seconds(entry.get("duration", entry.get("duration_seconds", 0))),
            "speakers": speakers,
            "transcript": entry.get("transcript", ""),
            "diarized_transcript": entry.get("diarized_transcript", []),
            "diarized_transcript_text": entry.get("diarized_transcript_text", ""),
            "executive_summary": entry.get("executive_summary", ""),
            "highlights": entry.get("highlights", []),
            "full_summary_sections": entry.get("full_summary_sections", []),
            "tasks": entry.get("tasks", []),
            "tags": entry.get("tags", []),
            "start_time": entry.get("start_time", ""),
            "end_time": entry.get("end_time", "")
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid meeting ID")

# Pydantic model for tag update
class TagUpdate(BaseModel):
    tags: List[str]

@app.patch("/api/meetings/{meeting_id}/tags")
async def update_meeting_tags(meeting_id: str, tag_update: TagUpdate):
    """Update tags for a specific meeting"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    try:
        idx = int(meeting_id)
        if idx < 0 or idx >= len(backend_app.chat_history):
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Update tags
        backend_app.chat_history[idx]["tags"] = tag_update.tags
        
        # Save to file
        import json
        with open(backend_app.history_file, 'w') as f:
            json.dump(backend_app.chat_history, f, indent=4)
        
        return {"success": True, "tags": tag_update.tags}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid meeting ID")

@app.get("/api/tags")
async def get_all_tags():
    """Get all unique tags from meetings"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    tags = set()
    for entry in backend_app.chat_history or []:
        if isinstance(entry, dict):
            for tag in entry.get("tags", []):
                tags.add(tag)
    
    # Add default tags if none exist
    if not tags:
        tags = {"Follow-up", "Important", "Meeting Notes"}
    
    return {"tags": sorted(list(tags))}

# ==================== TASKS ====================

@app.get("/api/tasks")
async def get_all_tasks():
    """Get all tasks extracted from meetings"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    history = backend_app.chat_history or []
    all_tasks = []
    
    for idx, entry in enumerate(history):
        if not isinstance(entry, dict):
            continue
        tasks = entry.get("tasks", [])
        meeting_title = entry.get("title", f"Meeting {idx + 1}")
        
        for task_idx, task in enumerate(tasks):
            if isinstance(task, str):
                all_tasks.append({
                    "id": f"{idx}-{task_idx}",
                    "meeting_id": str(idx),
                    "meeting_title": meeting_title,
                    "text": task,
                    "assignee": None,
                    "completed": False,
                    "date": entry.get("timestamp", entry.get("date", ""))
                })
            elif isinstance(task, dict):
                all_tasks.append({
                    "id": f"{idx}-{task_idx}",
                    "meeting_id": str(idx),
                    "meeting_title": meeting_title,
                    "text": task.get("task", task.get("text", task.get("action_item", ""))),
                    "assignee": task.get("assignee", task.get("speaker")),
                    "completed": task.get("completed", False),
                    "date": entry.get("timestamp", entry.get("date", ""))
                })
    
    return {"tasks": all_tasks}

# ==================== PEOPLE ====================

@app.get("/api/people")
async def get_people():
    """Get all people/speakers extracted from meetings"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    history = backend_app.chat_history or []
    people_map = {}
    
    for idx, entry in enumerate(history):
        if not isinstance(entry, dict):
            continue
        speaker_info = entry.get("speaker_info", {})
        meeting_date = entry.get("timestamp", entry.get("date", ""))
        
        # Handle different speaker_info formats
        speakers = []
        if isinstance(speaker_info, dict):
            speakers = speaker_info.get("list", [])
        elif isinstance(speaker_info, list):
            speakers = speaker_info
        
        for speaker in speakers:
            name = speaker if isinstance(speaker, str) else speaker.get("name", "Unknown") if isinstance(speaker, dict) else str(speaker)
            if not name or name == "Unknown":
                continue
            if name not in people_map:
                people_map[name] = {
                    "id": name.lower().replace(" ", "_").replace("(", "").replace(")", ""),
                    "name": name,
                    "email": None,
                    "last_meeting": meeting_date,
                    "meeting_count": 1
                }
            else:
                people_map[name]["meeting_count"] += 1
                if meeting_date and meeting_date > people_map[name]["last_meeting"]:
                    people_map[name]["last_meeting"] = meeting_date
    
    return {"people": list(people_map.values())}

# ==================== STORAGE ====================

@app.get("/api/storage/usage")
async def get_storage_usage():
    """Get disk usage for recordings directory."""
    import glob
    base_dir = backend_app.history_directory if backend_app else "~/Documents/Audio Recordings"
    base_dir = os.path.expanduser(base_dir)
    recordings_size = 0
    transcripts_size = 0
    try:
        for f in glob.glob(os.path.join(base_dir, "**/*.wav"), recursive=True):
            recordings_size += os.path.getsize(f)
        for f in glob.glob(os.path.join(base_dir, "**/*.txt"), recursive=True):
            transcripts_size += os.path.getsize(f)
    except Exception:
        pass
    history_size = 0
    try:
        hf = getattr(backend_app, 'history_file', 'audio_history.json')
        if os.path.exists(hf):
            history_size = os.path.getsize(hf)
    except Exception:
        pass
    return {
        "recordings_bytes": recordings_size,
        "transcripts_bytes": transcripts_size,
        "summaries_bytes": history_size,
        "total_bytes": recordings_size + transcripts_size + history_size,
        "storage_path": base_dir,
    }

# ==================== RECORDING PAUSE/RESUME ====================

@app.post("/api/recordings/pause")
async def pause_recording():
    """Pause the current recording."""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    if not backend_app.is_recording:
        raise HTTPException(status_code=409, detail="No recording in progress")
    backend_app.pause_recording()
    return {"success": True, "message": "Recording paused"}

@app.post("/api/recordings/resume")
async def resume_recording():
    """Resume a paused recording."""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    if not backend_app.is_recording:
        raise HTTPException(status_code=409, detail="No recording in progress")
    backend_app.resume_recording()
    return {"success": True, "message": "Recording resumed"}

# ==================== OLLAMA ====================

@app.get("/api/ollama/health")
async def ollama_health():
    """Check if Ollama is running and list available models."""
    try:
        resp = http_requests.get("http://localhost:11434/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return {"running": True, "models": models}
    except Exception:
        return {"running": False, "models": []}

# ==================== SETTINGS ====================

@app.get("/api/settings")
async def get_settings():
    """Get current app settings"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    # Access settings from the ConfigParser
    config = backend_app.config
    
    # Get API key status safely (check both config file and keychain)
    has_gemini_key = False
    try:
        gemini_key = config.get('API_KEYS', 'gemini', fallback='')
        has_gemini_key = bool(gemini_key and len(gemini_key) > 0)
        if not has_gemini_key:
            keychain_key = secure_store.get_api_key('gemini')
            has_gemini_key = bool(keychain_key)
    except Exception:
        pass

    # Get LLM provider
    llm_provider = "gemini"
    try:
        llm_provider = config.get('SETTINGS', 'default_llm', fallback='gemini')
    except Exception:
        pass

    # Get ollama model
    ollama_model = "llama3:8b"
    try:
        ollama_model = config.get('SETTINGS', 'ollama_model', fallback='llama3:8b')
    except Exception:
        pass
    
    # Check other API key statuses
    has_openai_key = bool(secure_store.get_api_key("openai"))
    has_anthropic_key = bool(secure_store.get_api_key("anthropic"))

    # General preferences
    launch_on_startup = True
    show_in_menubar = True
    dark_mode = True
    language = "en"
    try:
        if config.has_section("PREFERENCES"):
            launch_on_startup = config.getboolean("PREFERENCES", "launch_on_startup", fallback=True)
            show_in_menubar = config.getboolean("PREFERENCES", "show_in_menubar", fallback=True)
            dark_mode = config.getboolean("PREFERENCES", "dark_mode", fallback=True)
            language = config.get("PREFERENCES", "language", fallback="en")
    except Exception:
        pass

    # Obsidian settings
    obsidian_enabled = False
    obsidian_vault_path = ""
    obsidian_folder = "Meetings"
    try:
        if config.has_section("OBSIDIAN"):
            obsidian_enabled = config.getboolean("OBSIDIAN", "enabled", fallback=False)
            obsidian_vault_path = config.get("OBSIDIAN", "vault_path", fallback="")
            obsidian_folder = config.get("OBSIDIAN", "folder", fallback="Meetings")
    except Exception:
        pass

    return {
        "llm_provider": llm_provider,
        "gemini_model": "gemini-2.0-flash-exp",
        "ollama_model": ollama_model,
        "has_gemini_key": has_gemini_key,
        "has_openai_key": has_openai_key,
        "has_anthropic_key": has_anthropic_key,
        "recording_directory": backend_app.history_directory,
        "launch_on_startup": launch_on_startup,
        "show_in_menubar": show_in_menubar,
        "dark_mode": dark_mode,
        "language": language,
        "obsidian_enabled": obsidian_enabled,
        "obsidian_vault_path": obsidian_vault_path,
        "obsidian_folder": obsidian_folder,
    }

@app.put("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update app settings"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")

    # Update config file
    import configparser
    config_path = os.path.join(os.path.dirname(__file__), "audio_config.ini")
    config = configparser.ConfigParser()

    if os.path.exists(config_path):
        config.read(config_path)

    if not config.has_section("SETTINGS"):
        config.add_section("SETTINGS")

    # Store API keys in keychain (secure), NOT in the config file
    for provider, key_value in [("gemini", settings.gemini_api_key), ("openai", settings.openai_api_key), ("anthropic", settings.anthropic_api_key)]:
        if key_value:
            stored = secure_store.set_api_key(provider, key_value)
            if not stored:
                if not config.has_section("API_KEYS"):
                    config.add_section("API_KEYS")
                config.set("API_KEYS", provider, key_value)

    if settings.llm_provider:
        config.set("SETTINGS", "default_llm", settings.llm_provider)
    if settings.ollama_model:
        config.set("SETTINGS", "ollama_model", settings.ollama_model)

    # General preferences
    if any(v is not None for v in [settings.launch_on_startup, settings.show_in_menubar, settings.dark_mode, settings.language]):
        if not config.has_section("PREFERENCES"):
            config.add_section("PREFERENCES")
        if settings.launch_on_startup is not None:
            config.set("PREFERENCES", "launch_on_startup", str(settings.launch_on_startup))
        if settings.show_in_menubar is not None:
            config.set("PREFERENCES", "show_in_menubar", str(settings.show_in_menubar))
        if settings.dark_mode is not None:
            config.set("PREFERENCES", "dark_mode", str(settings.dark_mode))
        if settings.language is not None:
            config.set("PREFERENCES", "language", settings.language)

    # Obsidian settings
    if any(v is not None for v in [settings.obsidian_enabled, settings.obsidian_vault_path, settings.obsidian_folder]):
        if not config.has_section("OBSIDIAN"):
            config.add_section("OBSIDIAN")
        if settings.obsidian_enabled is not None:
            config.set("OBSIDIAN", "enabled", str(settings.obsidian_enabled))
        if settings.obsidian_vault_path is not None:
            config.set("OBSIDIAN", "vault_path", settings.obsidian_vault_path)
        if settings.obsidian_folder is not None:
            config.set("OBSIDIAN", "folder", settings.obsidian_folder)

    with open(config_path, "w") as f:
        config.write(f)

    # Reload backend config
    backend_app.load_config()

    return {"success": True, "message": "Settings updated"}



# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live updates (transcription, audio levels, status)"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive, receive any commands
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
    except Exception as e:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

# ==================== STATIC FILES + SPA FALLBACK ====================

# Mount static assets from the React build (JS, CSS, images)
if _FRONTEND_AVAILABLE:
    _ASSETS_DIR = os.path.join(_FRONTEND_DIR, "assets")
    if os.path.isdir(_ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="frontend-assets")

    # SPA catch-all: any route not matched by API returns index.html
    # so React Router can handle client-side routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes or WebSocket
        if full_path.startswith("api/") or full_path == "ws":
            raise HTTPException(status_code=404)
        # Try to serve static file first
        file_path = os.path.join(_FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Fall back to index.html for SPA routing
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    print("Starting Audio Summary API server...")
    if _FRONTEND_AVAILABLE:
        print(f"Frontend: http://localhost:8000  (serving from {_FRONTEND_DIR})")
    else:
        print("Frontend not found — API-only mode")
        print("To enable frontend, build figma-ui: cd figma-ui && npm run build")
    print("API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
