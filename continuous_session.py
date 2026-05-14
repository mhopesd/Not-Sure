"""Continuous-mode session: rolling-chunk diarized live transcription.

Owns the cross-chunk speaker identity logic that makes "Speaker_0" stay the
same person an hour into a recording. The rest of the app (backend.py /
api_server.py) treats this as a black box: feed it 20s WAV chunks, get back
a list of `Segment(speaker_id, start, end, text)` tuples whose `speaker_id`s
are stable across the whole session.
"""

from __future__ import annotations

import os
import json
import base64
import threading
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np

from app_logging import logger

# Heavy ML deps are imported lazily inside _ensure_models() so the app
# doesn't crash on import if continuous mode is unused or deps missing.
_FASTER_WHISPER_AVAILABLE = None
_PYANNOTE_AVAILABLE = None


@dataclass
class Segment:
    speaker_id: str          # Session-stable id e.g. "Speaker_0"
    start: float             # Absolute session-time seconds
    end: float
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


class ContinuousSessionUnavailable(RuntimeError):
    """Raised when continuous mode can't start (missing deps, no HF token, etc)."""


class ContinuousSession:
    """One continuous recording session with stable cross-chunk speakers.

    Thread-safety: `ingest_chunk` is called from a single worker thread;
    `rename_speaker` and `to_dict` may be called from request threads.
    """

    def __init__(
        self,
        session_id: str,
        hf_token: str,
        whisper_model_name: str = "small",
        embedding_threshold: float = 0.70,
    ):
        if not hf_token:
            raise ContinuousSessionUnavailable(
                "Continuous mode needs a HuggingFace token in audio_config.ini "
                "[CONTINUOUS] hf_token. See the config example for setup steps."
            )

        self.session_id = session_id
        self._hf_token = hf_token
        self._whisper_model_name = whisper_model_name
        self._embedding_threshold = embedding_threshold

        # Speaker registry. Each entry: {"centroid": np.ndarray, "n": int, "name": Optional[str]}
        self._speakers: dict[str, dict] = {}
        self._next_speaker_idx = 0
        self._segments: list[Segment] = []
        self._lock = threading.Lock()

        # Lazy-loaded models
        self._whisper = None
        self._diarization = None
        self._embedder = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def warmup(self) -> None:
        """Force model load now (call from a background thread at session start
        so the first chunk doesn't pay the cold-start cost)."""
        self._ensure_models()

    def ingest_chunk(self, wav_path: str, chunk_offset_seconds: float) -> list[Segment]:
        """Diarize + transcribe one chunk. Returns absolute-time segments.

        `chunk_offset_seconds` is added to each segment's start/end so the
        returned timestamps are session-relative, not chunk-relative.
        """
        if not os.path.exists(wav_path):
            logger.warning(f"ingest_chunk: missing wav {wav_path}")
            return []

        self._ensure_models()

        # 1. Diarize → list of (start, end, local_label)
        try:
            diarization = self._diarization(wav_path)
        except Exception as e:
            logger.error(f"ingest_chunk: diarization failed: {e}")
            return []

        diar_segments: list[tuple[float, float, str]] = [
            (turn.start, turn.end, label)
            for turn, _, label in diarization.itertracks(yield_label=True)
        ]

        if not diar_segments:
            logger.debug("ingest_chunk: no speech detected in chunk")
            return []

        # 2. Build local-label → session-wide speaker_id map for this chunk
        local_to_global = self._resolve_local_speakers(wav_path, diar_segments)

        # 3. Transcribe → list of (start, end, text)
        try:
            asr_segments_iter, _ = self._whisper.transcribe(
                wav_path, beam_size=1, vad_filter=True
            )
            asr_segments = [(s.start, s.end, s.text.strip()) for s in asr_segments_iter]
        except Exception as e:
            logger.error(f"ingest_chunk: whisper failed: {e}")
            return []

        # 4. Assign each ASR segment to the diarization segment with max overlap
        result: list[Segment] = []
        for a_start, a_end, text in asr_segments:
            if not text:
                continue
            best_label = self._best_overlap_label(a_start, a_end, diar_segments)
            speaker_id = local_to_global.get(best_label, self._mint_speaker(np.zeros(192)))
            seg = Segment(
                speaker_id=speaker_id,
                start=round(a_start + chunk_offset_seconds, 3),
                end=round(a_end + chunk_offset_seconds, 3),
                text=text,
            )
            result.append(seg)

        with self._lock:
            self._segments.extend(result)

        return result

    def rename_speaker(self, speaker_id: str, name: str) -> bool:
        with self._lock:
            if speaker_id not in self._speakers:
                return False
            self._speakers[speaker_id]["name"] = name.strip() or None
        return True

    def known_speakers(self) -> dict[str, Optional[str]]:
        """Map of speaker_id → human name (or None if unlabeled)."""
        with self._lock:
            return {sid: meta.get("name") for sid, meta in self._speakers.items()}

    def all_segments(self) -> list[Segment]:
        with self._lock:
            return list(self._segments)

    def to_dict(self) -> dict:
        """Serialize for crash-safe autosave / history."""
        with self._lock:
            return {
                "session_id": self.session_id,
                "speakers": {
                    sid: {
                        "name": meta.get("name"),
                        "n": meta["n"],
                        "centroid_b64": base64.b64encode(
                            meta["centroid"].astype(np.float32).tobytes()
                        ).decode("ascii"),
                    }
                    for sid, meta in self._speakers.items()
                },
                "segments": [s.to_dict() for s in self._segments],
                "next_speaker_idx": self._next_speaker_idx,
            }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_models(self) -> None:
        global _FASTER_WHISPER_AVAILABLE, _PYANNOTE_AVAILABLE

        if self._whisper is None:
            try:
                from faster_whisper import WhisperModel
                _FASTER_WHISPER_AVAILABLE = True
            except ImportError as e:
                _FASTER_WHISPER_AVAILABLE = False
                raise ContinuousSessionUnavailable(
                    f"faster-whisper not installed: {e}. Run `pip install faster-whisper`."
                )
            logger.info(f"Loading faster-whisper model '{self._whisper_model_name}'...")
            self._whisper = WhisperModel(
                self._whisper_model_name, device="auto", compute_type="int8"
            )

        if self._diarization is None or self._embedder is None:
            try:
                from pyannote.audio import Pipeline, Inference
                _PYANNOTE_AVAILABLE = True
            except ImportError as e:
                _PYANNOTE_AVAILABLE = False
                raise ContinuousSessionUnavailable(
                    f"pyannote.audio not installed: {e}. Run `pip install pyannote.audio`."
                )
            try:
                logger.info("Loading pyannote diarization + embedding models...")
                self._diarization = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self._hf_token,
                )
                self._embedder = Inference(
                    "pyannote/embedding",
                    window="whole",
                    use_auth_token=self._hf_token,
                )
            except Exception as e:
                raise ContinuousSessionUnavailable(
                    "Failed to load pyannote models. Confirm the HuggingFace "
                    "token is valid and you've accepted the model licenses at "
                    "hf.co/pyannote/speaker-diarization-3.1 and "
                    f"hf.co/pyannote/segmentation-3.0. Original error: {e}"
                )

    def _resolve_local_speakers(
        self, wav_path: str, diar_segments: list[tuple[float, float, str]]
    ) -> dict[str, str]:
        """For each local speaker label in the chunk, return its session id.

        Computes an embedding per local speaker from their concatenated audio,
        then matches to the registry by cosine similarity. Unmatched speakers
        get freshly minted ids; matched ones update the centroid (running mean).
        """
        # Group segments by local label
        by_label: dict[str, list[tuple[float, float]]] = {}
        for start, end, label in diar_segments:
            by_label.setdefault(label, []).append((start, end))

        # Load audio once (16kHz mono) using soundfile via pyannote helper
        import soundfile as sf
        audio, sr = sf.read(wav_path, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        local_to_global: dict[str, str] = {}
        for label, spans in by_label.items():
            # Concatenate all audio for this local speaker
            pieces = []
            for start, end in spans:
                i0 = max(0, int(start * sr))
                i1 = min(len(audio), int(end * sr))
                if i1 > i0:
                    pieces.append(audio[i0:i1])
            if not pieces:
                continue
            concat = np.concatenate(pieces)
            if len(concat) < int(0.5 * sr):
                # < 0.5s of audio — embedding will be noisy; skip matching
                # and tie to first existing speaker if any, else mint.
                if self._speakers:
                    local_to_global[label] = next(iter(self._speakers))
                else:
                    local_to_global[label] = self._mint_speaker(np.zeros(192))
                continue

            try:
                import torch
                waveform = torch.from_numpy(concat).unsqueeze(0)  # (1, n_samples)
                embedding = self._embedder(
                    {"waveform": waveform, "sample_rate": sr}
                )
                embedding = np.asarray(embedding).flatten()
            except Exception as e:
                logger.warning(f"embedding failed for local {label}: {e}")
                # Fallback: mint new speaker
                local_to_global[label] = self._mint_speaker(np.zeros(192))
                continue

            speaker_id = self._match_or_mint(embedding)
            local_to_global[label] = speaker_id

        return local_to_global

    def _match_or_mint(self, embedding: np.ndarray) -> str:
        """Find best-match speaker by cosine sim, or create a new one."""
        with self._lock:
            best_id: Optional[str] = None
            best_sim = -1.0
            for sid, meta in self._speakers.items():
                sim = _cosine(embedding, meta["centroid"])
                if sim > best_sim:
                    best_sim = sim
                    best_id = sid

            if best_id is not None and best_sim >= self._embedding_threshold:
                # Update centroid as running mean
                meta = self._speakers[best_id]
                n = meta["n"]
                meta["centroid"] = (meta["centroid"] * n + embedding) / (n + 1)
                meta["n"] = n + 1
                return best_id

            return self._mint_speaker_locked(embedding)

    def _mint_speaker(self, embedding: np.ndarray) -> str:
        with self._lock:
            return self._mint_speaker_locked(embedding)

    def _mint_speaker_locked(self, embedding: np.ndarray) -> str:
        speaker_id = f"Speaker_{self._next_speaker_idx}"
        self._next_speaker_idx += 1
        self._speakers[speaker_id] = {
            "centroid": embedding.astype(np.float32),
            "n": 1,
            "name": None,
        }
        return speaker_id

    @staticmethod
    def _best_overlap_label(
        a_start: float,
        a_end: float,
        diar_segments: list[tuple[float, float, str]],
    ) -> str:
        best_label = diar_segments[0][2]
        best_overlap = 0.0
        for d_start, d_end, label in diar_segments:
            overlap = max(0.0, min(a_end, d_end) - max(a_start, d_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_label = label
        return best_label


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))
