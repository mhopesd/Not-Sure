import { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Loader2, Calendar, Clock, Users, Sparkles } from 'lucide-react';
import { format } from 'date-fns';

interface Meeting {
  id: string;
  title: string;
  date: string;
  speakers: string[];
  transcript: string;
  nextSteps: string;
  duration: number;
}

interface MeetingHistoryProps {
  meetings: Meeting[];
  onAnalyzeMeeting: (meetingId: string) => Promise<void>;
}

export function MeetingHistory({ meetings, onAnalyzeMeeting }: MeetingHistoryProps) {
  const [expandedMeetingId, setExpandedMeetingId] = useState<string | null>(null);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);

  const toggleExpand = (meetingId: string) => {
    setExpandedMeetingId(expandedMeetingId === meetingId ? null : meetingId);
  };

  const handleAnalyze = async (meetingId: string) => {
    setAnalyzingId(meetingId);
    try {
      await onAnalyzeMeeting(meetingId);
    } finally {
      setAnalyzingId(null);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (meetings.length === 0) {
    return (
      <Card className="p-6">
        <p className="text-center text-gray-500">No meetings recorded yet</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {meetings.map((meeting) => {
        const isExpanded = expandedMeetingId === meeting.id;
        const isAnalyzing = analyzingId === meeting.id;

        return (
          <Card key={meeting.id} className="p-6">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="mb-2">{meeting.title}</h3>
                  
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {format(new Date(meeting.date), 'MMM d, yyyy')}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {format(new Date(meeting.date), 'h:mm a')}
                    </div>
                    {meeting.duration > 0 && (
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatDuration(meeting.duration)}
                      </div>
                    )}
                  </div>

                  {meeting.speakers.length > 0 && (
                    <div className="flex items-center gap-2 mt-2">
                      <Users className="w-4 h-4 text-gray-600" />
                      <div className="flex flex-wrap gap-1">
                        {meeting.speakers.map((speaker) => (
                          <Badge key={speaker} variant="outline">
                            {speaker}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <Button
                  onClick={() => toggleExpand(meeting.id)}
                  variant="outline"
                  size="sm"
                >
                  {isExpanded ? 'Collapse' : 'Expand'}
                </Button>
              </div>

              {isExpanded && (
                <div className="space-y-4 pt-4 border-t">
                  <div>
                    <h4 className="mb-2">Transcript</h4>
                    <div className="p-4 bg-gray-50 rounded-lg max-h-[300px] overflow-y-auto">
                      <p className="whitespace-pre-wrap text-sm">{meeting.transcript}</p>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4>Next Steps & Action Items</h4>
                      {!meeting.nextSteps && (
                        <Button
                          onClick={() => handleAnalyze(meeting.id)}
                          size="sm"
                          disabled={isAnalyzing}
                          className="gap-2"
                        >
                          {isAnalyzing ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Sparkles className="w-4 h-4" />
                          )}
                          Analyze with AI
                        </Button>
                      )}
                    </div>
                    {meeting.nextSteps ? (
                      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="whitespace-pre-wrap text-sm">{meeting.nextSteps}</p>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 italic">
                        Click "Analyze with AI" to generate action items and next steps
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
