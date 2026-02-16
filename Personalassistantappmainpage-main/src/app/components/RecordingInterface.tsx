import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Settings2, Sparkles, CheckCircle2, Lightbulb, Zap } from 'lucide-react';
import { MicrophoneSelector } from './MicrophoneSelector';
import { ProcessingProgress } from './ProcessingProgress';
import { getApiUrl, getApiHeaders } from '../config/api';

interface RecordingInterfaceProps {
  onRecordingComplete: () => void;
}

type RecordingState = 'idle' | 'selecting_mic' | 'recording' | 'processing' | 'complete';

export function RecordingInterface({ onRecordingComplete }: RecordingInterfaceProps) {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [duration, setDuration] = useState(0);
  const [selectedDevice, setSelectedDevice] = useState<string>('microphone');
  const [error, setError] = useState<string | null>(null);
  const [scratchpad, setScratchpad] = useState('');
  const [liveInsights, setLiveInsights] = useState<{
    key_points: string[];
    topic: string;
    meeting_type?: string;
    confidence?: number;
    action_items?: { text: string; assignee: string | null }[];
    decisions?: string[];
    sentiment?: string;
    suggested_questions?: string[];
  } | null>(null);

  const durationIntervalRef = useRef<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartClick = () => {
    setError(null);
    setRecordingState('selecting_mic');
  };

  const handleDeviceSelect = async (deviceId: string) => {
    setSelectedDevice(deviceId);
    await startRecording(deviceId);
  };

  const startRecording = async (deviceId: string) => {
    try {
      // Connect WebSocket for live updates
      connectWebSocket();

      // Start recording via API
      const response = await fetch(getApiUrl('/api/recordings/start'), {
        method: 'POST',
        headers: {
          ...getApiHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          device: deviceId,
          title: meetingTitle || undefined
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start recording');
      }

      setRecordingState('recording');
      setDuration(0);

      // Start duration counter
      durationIntervalRef.current = window.setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);

    } catch (err: any) {
      setError(err.message || 'Failed to start recording');
      setRecordingState('idle');
    }
  };

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws');

      ws.onopen = () => {
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
    }
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'transcript_update':
        // Live transcript updates could be shown here
        break;
      case 'audio_level':
        // Audio level for VU meter could be handled here
        break;
      case 'live_summary':
        if (message.data) {
          setLiveInsights(message.data);
        }
        break;
      case 'status':
        if (message.status === 'processing') {
          setRecordingState('processing');
        } else if (message.status === 'complete') {
          setRecordingState('complete');
        }
        break;
    }
  };

  const stopRecording = async () => {
    // Stop duration counter
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }

    try {
      const response = await fetch(getApiUrl('/api/recordings/stop'), {
        method: 'POST',
        headers: getApiHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to stop recording');
      }

      // Move to processing state - the backend will transcribe and summarize
      setRecordingState('processing');

    } catch (err: any) {
      setError(err.message || 'Failed to stop recording');
    }
  };

  const handleProcessingComplete = () => {
    setRecordingState('idle');
    setDuration(0);
    setMeetingTitle('');
    setScratchpad('');
    onRecordingComplete();
  };

  const isRecording = recordingState === 'recording';

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        {isRecording ? (
          <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
            <span>Meetings</span>
            <span>›</span>
            <span className="text-white">{meetingTitle || 'New Meeting'}</span>
          </div>
        ) : null}

        <h1 className="text-2xl font-bold text-white mb-3">
          {isRecording ? (meetingTitle || 'New Meeting') : 'Record Meeting'}
        </h1>

        {isRecording && (
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <span>Time</span>
              <span className="text-white">{formatDuration(duration)}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Tags</span>
              <button className="text-gray-400 hover:text-white flex items-center gap-1">
                <span className="text-lg">⊕</span> Add tag
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main content area */}
      {recordingState === 'idle' && (
        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Meeting title input */}
          <div className="w-full max-w-md mb-8">
            <input
              type="text"
              value={meetingTitle}
              onChange={(e) => setMeetingTitle(e.target.value)}
              placeholder="Meeting title (optional)"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#2774AE] transition-colors"
            />
          </div>

          {/* Start button */}
          <button
            onClick={handleStartClick}
            className="flex items-center gap-3 px-8 py-4 bg-[#2774AE] hover:bg-[#1e5f8e] rounded-xl text-white font-semibold text-lg transition-all transform hover:scale-105 shadow-lg shadow-[#2774AE]/25"
          >
            <Mic className="w-6 h-6" />
            Start Recording
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
        </div>
      )}

      {/* Recording state - show tabs and scratchpad */}
      {isRecording && (
        <div className="flex-1 flex flex-col">
          {/* Tabs */}
          <div className="flex gap-6 border-b border-white/10 mb-6">
            <button className="pb-3 text-white border-b-2 border-[#2774AE] font-medium">
              Scratchpad
            </button>
            <button className="pb-3 text-gray-400 hover:text-white transition-colors">
              Tasks
            </button>
          </div>

          {/* Scratchpad */}
          <div className="flex-1 mb-6">
            <textarea
              value={scratchpad}
              onChange={(e) => setScratchpad(e.target.value)}
              placeholder="Write private notes..."
              className="w-full h-full min-h-[200px] bg-transparent border-none text-white placeholder-gray-500 focus:outline-none resize-none"
            />
          </div>

          {/* Live Insights Panel */}
          {liveInsights && liveInsights.key_points && liveInsights.key_points.length > 0 && (
            <div className="mb-6 p-4 bg-[#2774AE]/10 border border-[#2774AE]/20 rounded-xl space-y-4">
              {/* Header row: title + meeting type badge + sentiment */}
              <div className="flex items-center gap-2 flex-wrap">
                <Sparkles className="w-4 h-4 text-[#FFD100]" />
                <span className="text-sm font-semibold text-white">Live Insights</span>
                {liveInsights.meeting_type && (
                  <span className="text-xs font-medium text-[#2774AE] bg-[#2774AE]/15 px-2 py-0.5 rounded-full capitalize">
                    {liveInsights.meeting_type.replace('_', ' ')}
                  </span>
                )}
                {liveInsights.topic && (
                  <span className="text-xs text-[#FFD100] bg-[#FFD100]/10 px-2 py-0.5 rounded">
                    {liveInsights.topic}
                  </span>
                )}
                {liveInsights.sentiment && liveInsights.sentiment !== 'neutral' && (
                  <span className="ml-auto text-xs text-gray-400 capitalize">
                    {liveInsights.sentiment === 'productive' ? '🟢' :
                      liveInsights.sentiment === 'tense' ? '🔴' :
                        liveInsights.sentiment === 'energetic' ? '⚡' :
                          liveInsights.sentiment === 'confused' ? '🟡' : '💬'}
                    {' '}{liveInsights.sentiment}
                  </span>
                )}
              </div>

              {/* Key points */}
              <ul className="space-y-1.5">
                {liveInsights.key_points.map((point, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-[#FFD100] mt-0.5">•</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>

              {/* Action items */}
              {liveInsights.action_items && liveInsights.action_items.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                    <span className="text-xs font-medium text-green-400 uppercase tracking-wide">Action Items</span>
                  </div>
                  <ul className="space-y-1.5">
                    {liveInsights.action_items.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                        <span className="text-green-400 mt-0.5">☐</span>
                        <span>
                          {item.text}
                          {item.assignee && (
                            <span className="ml-1 text-xs text-[#2774AE] bg-[#2774AE]/10 px-1.5 py-0.5 rounded">{item.assignee}</span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Decisions */}
              {liveInsights.decisions && liveInsights.decisions.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Zap className="w-3.5 h-3.5 text-[#FFD100]" />
                    <span className="text-xs font-medium text-[#FFD100] uppercase tracking-wide">Decisions</span>
                  </div>
                  <ul className="space-y-1.5">
                    {liveInsights.decisions.map((decision, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                        <span className="text-[#FFD100] mt-0.5">✓</span>
                        <span>{decision}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggested questions */}
              {liveInsights.suggested_questions && liveInsights.suggested_questions.length > 0 && (
                <div className="pt-2 border-t border-white/5">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Lightbulb className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-xs font-medium text-blue-400 uppercase tracking-wide">Try Asking</span>
                  </div>
                  {liveInsights.suggested_questions.map((q, idx) => (
                    <p key={idx} className="text-sm text-gray-400 italic">"{q}"</p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Info message */}
          <div className="text-center text-gray-500 text-sm mb-6">
            {liveInsights ? 'Insights updating as the conversation continues...' : 'Transcript and summary will be generated once the meeting is over'}
          </div>

          {/* Recording controls - fixed at bottom */}
          <div className="flex items-center justify-center gap-4 py-4 bg-[#1a1a1a] rounded-xl">
            <span className="text-white font-mono text-lg">{formatDuration(duration)}</span>

            <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
              <Settings2 className="w-5 h-5 text-gray-400" />
            </button>

            <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
              <Mic className="w-5 h-5 text-gray-400" />
            </button>

            <button
              onClick={stopRecording}
              className="flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-700 rounded-lg text-white font-medium transition-colors"
            >
              <Square className="w-4 h-4 fill-current" />
              Stop
            </button>
          </div>
        </div>
      )}

      {/* Processing state */}
      {recordingState === 'processing' && (
        <div className="flex-1">
          <ProcessingProgress
            isVisible={true}
            meetingTitle={meetingTitle || 'New Meeting'}
            onComplete={handleProcessingComplete}
          />
        </div>
      )}

      {/* Microphone selector modal */}
      <MicrophoneSelector
        isOpen={recordingState === 'selecting_mic'}
        onClose={() => setRecordingState('idle')}
        onSelect={handleDeviceSelect}
      />
    </div>
  );
}