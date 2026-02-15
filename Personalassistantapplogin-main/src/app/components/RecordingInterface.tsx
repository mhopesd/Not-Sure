import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Mic, Square, Loader2 } from 'lucide-react';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';

interface RecordingInterfaceProps {
  onSaveRecording: (data: {
    title: string;
    speakers: string[];
    transcript: string;
    duration: number;
  }) => void;
}

export function RecordingInterface({ onSaveRecording }: RecordingInterfaceProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [speakers, setSpeakers] = useState<string[]>([]);
  const [currentSpeaker, setCurrentSpeaker] = useState('');
  const [duration, setDuration] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [microphoneError, setMicrophoneError] = useState<string | null>(null);
  
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
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
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

  const startRecording = async () => {
    setMicrophoneError(null); // Clear any previous errors
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

  const stopRecording = () => {
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
  };

  const handleAddSpeaker = () => {
    if (currentSpeaker.trim() && !speakers.includes(currentSpeaker.trim())) {
      setSpeakers([...speakers, currentSpeaker.trim()]);
      setCurrentSpeaker('');
    }
  };

  const handleRemoveSpeaker = (speaker: string) => {
    setSpeakers(speakers.filter(s => s !== speaker));
  };

  const handleSave = async () => {
    if (!transcript.trim()) {
      alert('Please ensure there is a transcript to save.');
      return;
    }

    setIsSaving(true);
    try {
      await onSaveRecording({
        title: meetingTitle.trim() || 'Untitled Meeting',
        speakers,
        transcript,
        duration
      });

      // Reset form
      setMeetingTitle('');
      setSpeakers([]);
      setTranscript('');
      setDuration(0);
    } catch (error) {
      console.error('Error saving recording:', error);
      alert('Failed to save recording');
    } finally {
      setIsSaving(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <h2 className="mb-4">Record Meeting</h2>
          
          <div className="flex items-center gap-4 mb-6">
            {!isRecording ? (
              <Button onClick={startRecording} className="gap-2" size="lg">
                <Mic className="w-5 h-5" />
                Start Recording
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
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="meeting-title" className="mb-2 block">Meeting Title (optional)</Label>
              <Input
                id="meeting-title"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                placeholder="Enter meeting title"
                disabled={isRecording}
              />
            </div>

            <div>
              <Label htmlFor="speakers" className="mb-2 block">Speakers (optional)</Label>
              <div className="flex gap-2 mb-2">
                <Input
                  id="speakers"
                  value={currentSpeaker}
                  onChange={(e) => setCurrentSpeaker(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddSpeaker()}
                  placeholder="Add speaker name"
                  disabled={isRecording}
                />
                <Button onClick={handleAddSpeaker} variant="outline" disabled={isRecording}>
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {speakers.map((speaker) => (
                  <Badge key={speaker} variant="secondary">
                    {speaker}
                    {!isRecording && (
                      <button
                        onClick={() => handleRemoveSpeaker(speaker)}
                        className="ml-1 hover:text-red-600"
                      >
                        ×
                      </button>
                    )}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>

        {transcript && (
          <div>
            <Label>Transcript</Label>
            <div className="mt-2 p-4 bg-gray-50 rounded-lg border min-h-[200px] max-h-[400px] overflow-y-auto">
              <p className="whitespace-pre-wrap">{transcript}</p>
            </div>
            
            {!isRecording && (
              <Button 
                onClick={handleSave} 
                className="mt-4"
                disabled={isSaving}
              >
                {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Save Meeting
              </Button>
            )}
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

        {microphoneError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">
              <strong>Microphone Error:</strong> {microphoneError}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}