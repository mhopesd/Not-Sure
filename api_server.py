"""
FastAPI Server - Audio Summary App Backend API

This server exposes the Python backend (audio recording, transcription, summarization)
as REST and WebSocket endpoints for the React frontend.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import os
from datetime import datetime
import threading
import logging

# Import the existing backend
from backend import EnhancedAudioApp

# Import integrations
from integrations import OAuthManager, MicrosoftIntegration, GoogleIntegration

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Summary API",
    description="Local API for audio recording, transcription, and AI summarization",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global backend instance
backend_app: Optional[EnhancedAudioApp] = None
active_websockets: List[WebSocket] = []
oauth_manager: Optional[OAuthManager] = None

# Pydantic models
class RecordingStartRequest(BaseModel):
    title: Optional[str] = None
    speakers: Optional[List[str]] = []

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
    ollama_model: Optional[str] = None
    llm_provider: Optional[str] = None

# Status callback for WebSocket updates
async def broadcast_status(message: str):
    """Send status updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "status", "message": message})
        except:
            pass

async def broadcast_transcript(text: str):
    """Send live transcript updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "transcript", "text": text})
        except:
            pass

async def broadcast_level(level: float):
    """Send audio level updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "level", "value": level})
        except:
            pass

async def broadcast_live_summary(data: dict):
    """Send live summary updates to all connected WebSocket clients"""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "live_summary", "data": data})
        except:
            pass

# Thread-safe status callback wrapper
def status_callback(message: str):
    asyncio.create_task(broadcast_status(message))

def transcript_callback(text: str):
    asyncio.create_task(broadcast_transcript(text))

def level_callback(level: float):
    asyncio.create_task(broadcast_level(level))

def live_summary_callback(data: dict):
    asyncio.create_task(broadcast_live_summary(data))

@app.on_event("startup")
async def startup():
    """Initialize the backend on server start"""
    global backend_app, oauth_manager
    backend_app = EnhancedAudioApp()
    backend_app.summary_callback = live_summary_callback
    oauth_manager = OAuthManager()
    print("✓ Backend initialized")
    print("✓ OAuth manager initialized")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Audio Summary API is running"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "backend_ready": backend_app is not None,
        "model_loaded": backend_app.whisper_model is not None if backend_app else False
    }

# ==================== DEVICES ====================

@app.get("/api/devices")
async def get_devices():
    """Get available audio input devices"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    backend_app.detect_devices()
    return {
        "devices": [
            {"id": "microphone", "name": "Microphone", "available": backend_app.microphone_device is not None},
            {"id": "system", "name": "System Audio (BlackHole)", "available": backend_app.blackhole_device is not None},
            {"id": "hybrid", "name": "Hybrid (BBrew)", "available": backend_app.hybrid_device is not None},
        ],
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
    
    # Start recording in background thread
    threading.Thread(target=backend_app.start_recording, daemon=True).start()
    
    return {
        "success": True,
        "message": "Recording started",
        "title": request.title
    }

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
    """Get current recording status"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    return {
        "is_recording": backend_app.is_recording,
        "duration": 0  # TODO: Track actual duration
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
            "duration": entry.get("duration", entry.get("duration_seconds", 0)),
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
            "duration": entry.get("duration", entry.get("duration_seconds", 0)),
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

# ==================== SEARCH ====================

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

# ==================== JOURNAL ====================

class JournalEntry(BaseModel):
    entry: str

@app.get("/api/journal")
async def get_journal_entries():
    """Get all journal entries"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    entries = backend_app.get_journal_entries()
    return {"entries": entries}

@app.post("/api/journal")
async def create_journal_entry(journal: JournalEntry):
    """Create a new journal entry"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    entry = backend_app.create_journal_entry(journal.entry)
    return {"journalEntry": entry}

@app.put("/api/journal/{entry_id}/optimize")
async def optimize_journal_entry(entry_id: str):
    """Optimize a journal entry with AI suggestions"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    suggestions = backend_app.optimize_journal_entry(entry_id)
    return {
        "journalEntry": {
            "id": entry_id,
            "suggestions": suggestions
        }
    }

# ==================== SETTINGS ====================

@app.get("/api/settings")
async def get_settings():
    """Get current app settings"""
    if not backend_app:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    # Access settings from the ConfigParser
    config = backend_app.config
    
    # Get API key status safely
    has_gemini_key = False
    try:
        gemini_key = config.get('API_KEYS', 'gemini', fallback='')
        has_gemini_key = bool(gemini_key and len(gemini_key) > 0)
    except:
        pass
    
    # Get LLM provider
    llm_provider = "gemini"
    try:
        llm_provider = config.get('SETTINGS', 'default_llm', fallback='gemini')
    except:
        pass
    
    # Get ollama model
    ollama_model = "llama3:8b"
    try:
        ollama_model = config.get('SETTINGS', 'ollama_model', fallback='llama3:8b')
    except:
        pass
    
    return {
        "llm_provider": llm_provider,
        "gemini_model": "gemini-2.0-flash-exp",
        "ollama_model": ollama_model,
        "has_gemini_key": has_gemini_key,
        "recording_directory": backend_app.history_directory
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
    
    # Use the correct section names from the backend
    if not config.has_section("API_KEYS"):
        config.add_section("API_KEYS")
    if not config.has_section("SETTINGS"):
        config.add_section("SETTINGS")
    
    if settings.gemini_api_key:
        config.set("API_KEYS", "gemini", settings.gemini_api_key)
    if settings.llm_provider:
        config.set("SETTINGS", "default_llm", settings.llm_provider)
    if settings.ollama_model:
        config.set("SETTINGS", "ollama_model", settings.ollama_model)
    
    with open(config_path, "w") as f:
        config.write(f)
    
    # Reload backend config
    backend_app.load_config()
    
    return {"success": True, "message": "Settings updated"}

# ==================== INTEGRATIONS ====================

MICROSOFT_REDIRECT_URI = "http://localhost:8000/api/integrations/microsoft/callback"
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/integrations/google/callback"


class IntegrationCredentials(BaseModel):
    provider: str  # "microsoft" or "google"
    client_id: str
    client_secret: str


class CalendarEventCreate(BaseModel):
    provider: str  # "microsoft" or "google"
    title: str
    start: str  # ISO 8601
    end: str    # ISO 8601
    description: str = ""
    location: str = ""


class EmailSend(BaseModel):
    provider: str  # "microsoft" or "google"
    to: str
    subject: str
    body_html: str


def _ensure_valid_token(provider: str) -> str:
    """Get a valid access token, refreshing if expired. Returns the access token."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")

    tokens = oauth_manager.load_tokens(provider)
    if not tokens:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    # Check if token needs refresh
    if oauth_manager.is_token_expired(provider):
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            oauth_manager.clear_tokens(provider)
            raise HTTPException(status_code=401, detail=f"{provider} token expired, please reconnect")

        creds = oauth_manager.get_credentials(provider)
        if not creds:
            raise HTTPException(status_code=400, detail=f"No credentials for {provider}")

        try:
            if provider == "microsoft":
                new_tokens = MicrosoftIntegration.refresh_tokens(
                    refresh_token, creds["client_id"], creds["client_secret"]
                )
            else:
                new_tokens = GoogleIntegration.refresh_tokens(
                    refresh_token, creds["client_id"], creds["client_secret"]
                )
            # Preserve email/display_name from old tokens
            new_tokens["email"] = tokens.get("email", "")
            new_tokens["display_name"] = tokens.get("display_name", "")
            oauth_manager.save_tokens(provider, new_tokens)
            return new_tokens["access_token"]
        except Exception as e:
            logger.error("Token refresh failed for %s: %s", provider, e)
            oauth_manager.clear_tokens(provider)
            raise HTTPException(status_code=401, detail=f"Token refresh failed, please reconnect")

    return tokens["access_token"]


# HTML page returned after OAuth callback — closes popup and notifies parent
_OAUTH_SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Connected!</title></head>
<body style="font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0fdf4;">
  <div style="text-align: center; padding: 2rem;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">✅</div>
    <h2 style="color: #16a34a;">Successfully Connected!</h2>
    <p style="color: #6b7280;">You can close this window.</p>
  </div>
  <script>
    if (window.opener) {
      window.opener.postMessage({ type: 'oauth_success', provider: '%PROVIDER%' }, '*');
    }
    setTimeout(() => window.close(), 2000);
  </script>
</body>
</html>
"""

_OAUTH_ERROR_HTML = """
<!DOCTYPE html>
<html>
<head><title>Connection Failed</title></head>
<body style="font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #fef2f2;">
  <div style="text-align: center; padding: 2rem;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">❌</div>
    <h2 style="color: #dc2626;">Connection Failed</h2>
    <p style="color: #6b7280;">%ERROR%</p>
  </div>
  <script>
    if (window.opener) {
      window.opener.postMessage({ type: 'oauth_error', provider: '%PROVIDER%', error: '%ERROR%' }, '*');
    }
    setTimeout(() => window.close(), 5000);
  </script>
</body>
</html>
"""


@app.put("/api/integrations/credentials")
async def save_integration_credentials(creds: IntegrationCredentials):
    """Save OAuth client credentials for a provider."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")
    if creds.provider not in OAuthManager.PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {creds.provider}")

    oauth_manager.save_credentials(creds.provider, creds.client_id, creds.client_secret)
    return {"success": True, "message": f"Credentials saved for {creds.provider}"}


@app.get("/api/integrations/status")
async def get_integration_status():
    """Get connection status for all integration providers."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")
    return oauth_manager.get_all_status()


# ── Microsoft OAuth ────────────────────────────────────────────────

@app.get("/api/integrations/microsoft/auth")
async def microsoft_auth():
    """Generate Microsoft OAuth authorization URL."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")

    creds = oauth_manager.get_credentials("microsoft")
    if not creds:
        raise HTTPException(
            status_code=400,
            detail="Microsoft credentials not configured. Please save your Client ID and Secret first."
        )

    auth_url = MicrosoftIntegration.get_auth_url(
        client_id=creds["client_id"],
        redirect_uri=MICROSOFT_REDIRECT_URI,
        state="microsoft",
    )
    return {"auth_url": auth_url}


@app.get("/api/integrations/microsoft/callback")
async def microsoft_callback(code: str = None, error: str = None, state: str = None):
    """Handle Microsoft OAuth callback — exchanges code for tokens."""
    if error:
        html = _OAUTH_ERROR_HTML.replace("%PROVIDER%", "microsoft").replace("%ERROR%", error)
        return HTMLResponse(content=html)

    if not code:
        html = _OAUTH_ERROR_HTML.replace("%PROVIDER%", "microsoft").replace("%ERROR%", "No authorization code received")
        return HTMLResponse(content=html)

    try:
        creds = oauth_manager.get_credentials("microsoft")
        if not creds:
            raise ValueError("Microsoft credentials not configured")

        token_data = MicrosoftIntegration.exchange_code(
            code=code,
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
            redirect_uri=MICROSOFT_REDIRECT_URI,
        )
        oauth_manager.save_tokens("microsoft", token_data)
        logger.info("Microsoft OAuth completed for %s", token_data.get("email"))

        html = _OAUTH_SUCCESS_HTML.replace("%PROVIDER%", "microsoft")
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error("Microsoft OAuth error: %s", e)
        html = _OAUTH_ERROR_HTML.replace("%PROVIDER%", "microsoft").replace("%ERROR%", str(e))
        return HTMLResponse(content=html)


@app.delete("/api/integrations/microsoft/disconnect")
async def microsoft_disconnect():
    """Disconnect Microsoft integration."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")
    oauth_manager.clear_tokens("microsoft")
    return {"success": True, "message": "Microsoft disconnected"}


# ── Google OAuth ───────────────────────────────────────────────────

@app.get("/api/integrations/google/auth")
async def google_auth():
    """Generate Google OAuth authorization URL."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")

    creds = oauth_manager.get_credentials("google")
    if not creds:
        raise HTTPException(
            status_code=400,
            detail="Google credentials not configured. Please save your Client ID and Secret first."
        )

    auth_url = GoogleIntegration.get_auth_url(
        client_id=creds["client_id"],
        redirect_uri=GOOGLE_REDIRECT_URI,
        state="google",
    )
    return {"auth_url": auth_url}


@app.get("/api/integrations/google/callback")
async def google_callback(code: str = None, error: str = None, state: str = None):
    """Handle Google OAuth callback — exchanges code for tokens."""
    if error:
        html = _OAUTH_ERROR_HTML.replace("%PROVIDER%", "google").replace("%ERROR%", error)
        return HTMLResponse(content=html)

    if not code:
        html = _OAUTH_ERROR_HTML.replace("%PROVIDER%", "google").replace("%ERROR%", "No authorization code received")
        return HTMLResponse(content=html)

    try:
        creds = oauth_manager.get_credentials("google")
        if not creds:
            raise ValueError("Google credentials not configured")

        token_data = GoogleIntegration.exchange_code(
            code=code,
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        oauth_manager.save_tokens("google", token_data)
        logger.info("Google OAuth completed for %s", token_data.get("email"))

        html = _OAUTH_SUCCESS_HTML.replace("%PROVIDER%", "google")
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error("Google OAuth error: %s", e)
        html = _OAUTH_ERROR_HTML.replace("%PROVIDER%", "google").replace("%ERROR%", str(e))
        return HTMLResponse(content=html)


@app.delete("/api/integrations/google/disconnect")
async def google_disconnect():
    """Disconnect Google integration."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")
    oauth_manager.clear_tokens("google")
    return {"success": True, "message": "Google disconnected"}


# ── Calendar & Email (unified) ─────────────────────────────────────

@app.get("/api/integrations/calendar/events")
async def get_calendar_events(days_ahead: int = 7):
    """Get calendar events from all connected providers."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")

    all_events = []

    # Microsoft Calendar
    if oauth_manager.is_connected("microsoft"):
        try:
            access_token = _ensure_valid_token("microsoft")
            events = MicrosoftIntegration.get_calendar_events(access_token, days_ahead)
            all_events.extend(events)
        except Exception as e:
            logger.warning("Failed to fetch Microsoft calendar: %s", e)

    # Google Calendar
    if oauth_manager.is_connected("google"):
        try:
            access_token = _ensure_valid_token("google")
            events = GoogleIntegration.get_calendar_events(access_token, days_ahead)
            all_events.extend(events)
        except Exception as e:
            logger.warning("Failed to fetch Google calendar: %s", e)

    # Sort all events by start time
    all_events.sort(key=lambda e: e.get("start", ""))
    return {"events": all_events}


@app.post("/api/integrations/calendar/events")
async def create_calendar_event(event: CalendarEventCreate):
    """Create a calendar event on a connected provider."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")
    if event.provider not in OAuthManager.PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {event.provider}")

    access_token = _ensure_valid_token(event.provider)

    try:
        if event.provider == "microsoft":
            result = MicrosoftIntegration.create_calendar_event(
                access_token, event.title, event.start, event.end,
                body=event.description, location=event.location,
            )
        else:
            result = GoogleIntegration.create_calendar_event(
                access_token, event.title, event.start, event.end,
                description=event.description, location=event.location,
            )
        return {"success": True, "event": result}
    except Exception as e:
        logger.error("Failed to create calendar event: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/integrations/email/send")
async def send_email(email: EmailSend):
    """Send an email via a connected provider (meeting summary sharing)."""
    if not oauth_manager:
        raise HTTPException(status_code=503, detail="OAuth manager not initialized")
    if email.provider not in OAuthManager.PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {email.provider}")

    access_token = _ensure_valid_token(email.provider)

    try:
        if email.provider == "microsoft":
            MicrosoftIntegration.send_email(
                access_token, email.to, email.subject, email.body_html,
            )
        else:
            GoogleIntegration.send_email(
                access_token, email.to, email.subject, email.body_html,
            )
        return {"success": True, "message": f"Email sent via {email.provider}"}
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

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
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
    except Exception as e:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    print("Starting Audio Summary API server...")
    print("Frontend should connect to: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
