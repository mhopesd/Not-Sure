import { useState, useRef, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Loader2, Sparkles, Calendar, Lightbulb, Mic, Square } from 'lucide-react';
import { format } from 'date-fns';
import { projectId, publicAnonKey } from '../../../utils/supabase/info';

interface JournalEntry {
  id: string;
  date: string;
  entry: string;
  transcript?: string;
  aiSuggestions: string;
}

interface JournalInterfaceProps {
  entries: JournalEntry[];
  onCreateEntry: (entry: string) => Promise<void>;
  onOptimizeEntry: (entryId: string) => Promise<void>;
}

export function JournalInterface({ entries, onCreateEntry, onOptimizeEntry }: JournalInterfaceProps) {
  const [newEntry, setNewEntry] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [optimizingId, setOptimizingId] = useState<string | null>(null);
  const [expandedEntryId, setExpandedEntryId] = useState<string | null>(null);
  
  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [duration, setDuration] = useState(0);
  const [microphoneError, setMicrophoneError] = useState<string | null>(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recognitionRef = useRef<any>(null);
  const durationIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    // Check if browser supports Speech Recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          }
        }

        if (finalTranscript) {
          setTranscript(prev => prev + finalTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
      };

      recognitionRef.current = recognition;
    }
  }, []);
  
  const handleCreateEntry = async () => {
    if (!newEntry.trim() && !transcript.trim()) {
      alert('Please write something in your journal entry');
      return;
    }

    setIsCreating(true);
    try {
      await onCreateEntry(newEntry || transcript);
      setNewEntry('');
      setTranscript('');
    } finally {
      setIsCreating(false);
    }
  };

  const handleOptimize = async (entryId: string) => {
    setOptimizingId(entryId);
    try {
      await onOptimizeEntry(entryId);
    } finally {
      setOptimizingId(null);
    }
  };

  const toggleExpand = (entryId: string) => {
    setExpandedEntryId(expandedEntryId === entryId ? null : entryId);
  };

  const startRecording = async () => {
    setMicrophoneError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks: Blob[] = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setTranscript('');
      setDuration(0);

      // Start speech recognition if available
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }

      // Start duration counter
      durationIntervalRef.current = window.setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    } catch (error: any) {
      console.error('Error accessing microphone:', error);
      
      let errorMessage = 'Could not access microphone. ';
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMessage += 'Microphone permission was denied. Please click the camera/microphone icon in your browser\'s address bar and allow microphone access, then try again.';
      } else if (error.name === 'NotFoundError') {
        errorMessage += 'No microphone was found. Please connect a microphone and try again.';
      } else if (error.name === 'NotReadableError') {
        errorMessage += 'Your microphone is already in use by another application.';
      } else {
        errorMessage += 'Please check your browser settings and ensure microphone access is enabled.';
      }
      
      setMicrophoneError(errorMessage);
    }
  };

  const stopRecording = async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }

    setIsRecording(false);
    
    // Generate AI summary from transcript
    if (transcript.trim()) {
      await generateSummary(transcript);
    }
  };

  const generateSummary = async (transcriptText: string) => {
    setIsGeneratingSummary(true);
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/journal/summarize`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ transcript: transcriptText }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setNewEntry(data.summary);
      } else {
        console.error('Failed to generate summary:', await response.text());
      }
    } catch (error) {
      console.error('Error generating summary:', error);
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="mb-2">New Journal Entry</h2>
        <div className="space-y-4">
          {/* Voice Recording Section */}
          <div className="flex items-center gap-4 -mt-2">
            {!isRecording ? (
              <Button onClick={startRecording} className="gap-2" size="lg" disabled={isGeneratingSummary}>
                <Mic className="w-5 h-5" />
                Record Voice Entry
              </Button>
            ) : (
              <Button onClick={stopRecording} variant="destructive" className="gap-2" size="lg">
                <Square className="w-5 h-5" />
                Stop Recording
              </Button>
            )}
            
            {isRecording && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
                <span className="text-sm">{formatDuration(duration)}</span>
              </div>
            )}
            
            {isGeneratingSummary && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating summary...
              </div>
            )}
          </div>
          
          {microphoneError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                <strong>Microphone Error:</strong> {microphoneError}
              </p>
            </div>
          )}
          
          {!recognitionRef.current && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> Speech recognition is not supported in your browser. 
                Recording will continue, but live transcription is unavailable.
              </p>
            </div>
          )}

          {transcript && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="text-sm mb-2">Voice Transcript:</h4>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{transcript}</p>
            </div>
          )}

          <div>
            <label className="text-sm mb-2 block">Journal Entry (or edit summary below):</label>
            <Textarea
              value={newEntry}
              onChange={(e) => setNewEntry(e.target.value)}
              placeholder="Write about your day, your goals, challenges, or what you're working on..."
              className="min-h-[200px]"
              disabled={isRecording}
            />
          </div>
          
          <Button
            onClick={handleCreateEntry}
            disabled={isCreating || isRecording || isGeneratingSummary || (!newEntry.trim() && !transcript.trim())}
          >
            {isCreating && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Save Entry
          </Button>
        </div>
      </Card>

      <div>
        <h2 className="mb-4">Journal History</h2>
        {entries.length === 0 ? (
          <Card className="p-6">
            <p className="text-center text-gray-500">No journal entries yet</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => {
              const isExpanded = expandedEntryId === entry.id;
              const isOptimizing = optimizingId === entry.id;

              return (
                <Card key={entry.id} className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        {format(new Date(entry.date), 'EEEE, MMMM d, yyyy')} at {format(new Date(entry.date), 'h:mm a')}
                      </div>
                      <Button
                        onClick={() => toggleExpand(entry.id)}
                        variant="outline"
                        size="sm"
                      >
                        {isExpanded ? 'Collapse' : 'Expand'}
                      </Button>
                    </div>

                    {isExpanded && (
                      <div className="space-y-4 pt-4 border-t">
                        <div>
                          <h4 className="mb-2">Entry</h4>
                          <div className="p-4 bg-gray-50 rounded-lg">
                            <p className="whitespace-pre-wrap text-sm">{entry.entry}</p>
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="flex items-center gap-2">
                              <Lightbulb className="w-4 h-4" />
                              AI-Optimized Next Steps
                            </h4>
                            {!entry.aiSuggestions && (
                              <Button
                                onClick={() => handleOptimize(entry.id)}
                                size="sm"
                                disabled={isOptimizing}
                                className="gap-2"
                              >
                                {isOptimizing ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Sparkles className="w-4 h-4" />
                                )}
                                Get AI Suggestions
                              </Button>
                            )}
                          </div>
                          {entry.aiSuggestions ? (
                            <div className="p-4 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                              <p className="whitespace-pre-wrap text-sm">{entry.aiSuggestions}</p>
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 italic">
                              Click "Get AI Suggestions" to receive optimized steps for your journey
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {!isExpanded && (
                      <div className="pt-2">
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {entry.entry}
                        </p>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}