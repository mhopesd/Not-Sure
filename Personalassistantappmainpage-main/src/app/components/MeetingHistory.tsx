import { useState, useMemo } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Loader2, Calendar, Clock, Users, Sparkles, Tag, MoreHorizontal } from 'lucide-react';
import { format, isToday, isTomorrow, isThisWeek, isThisMonth, parseISO } from 'date-fns';
import { TagFilter } from './TagFilter';

interface Meeting {
  id: string;
  title: string;
  date: string;
  speakers: string[];
  transcript: string;
  nextSteps: string;
  duration: number;
  tags?: string[];
}

interface MeetingHistoryProps {
  meetings: Meeting[];
  onAnalyzeMeeting: (meetingId: string) => Promise<void>;
  onMeetingClick?: (meetingId: string) => void;
}

// Group meetings by date category
function groupMeetingsByDate(meetings: Meeting[]): { label: string; meetings: Meeting[] }[] {
  const groups: { [key: string]: Meeting[] } = {};
  const now = new Date();

  meetings.forEach((meeting) => {
    let label: string;
    try {
      const meetingDate = parseISO(meeting.date);

      if (isToday(meetingDate)) {
        label = 'Today';
      } else if (isTomorrow(meetingDate)) {
        label = 'Coming up';
      } else if (meetingDate > now) {
        label = 'Coming up';
      } else if (isThisWeek(meetingDate)) {
        label = 'This week';
      } else if (isThisMonth(meetingDate)) {
        label = 'This month';
      } else {
        label = format(meetingDate, 'MMM d, yyyy');
      }
    } catch {
      label = 'Other';
    }

    if (!groups[label]) {
      groups[label] = [];
    }
    groups[label].push(meeting);
  });

  // Sort groups with "Coming up" first, then by date
  const sortedLabels = Object.keys(groups).sort((a, b) => {
    if (a === 'Coming up') return -1;
    if (b === 'Coming up') return 1;
    if (a === 'Today') return -1;
    if (b === 'Today') return 1;
    if (a === 'This week') return -1;
    if (b === 'This week') return 1;
    return 0;
  });

  return sortedLabels.map((label) => ({
    label,
    meetings: groups[label],
  }));
}

export function MeetingHistory({ meetings, onAnalyzeMeeting, onMeetingClick }: MeetingHistoryProps) {
  const [expandedMeetingId, setExpandedMeetingId] = useState<string | null>(null);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Extract all unique tags from meetings
  const availableTags = useMemo(() => {
    const tags = new Set<string>();
    meetings.forEach((m) => m.tags?.forEach((t) => tags.add(t)));
    // Add some default tags if none exist
    if (tags.size === 0) {
      ['Follow-up', 'Important', 'Meeting Notes'].forEach(t => tags.add(t));
    }
    return Array.from(tags);
  }, [meetings]);

  // Filter meetings by selected tags
  const filteredMeetings = useMemo(() => {
    if (selectedTags.length === 0) return meetings;
    return meetings.filter((m) =>
      m.tags?.some((t) => selectedTags.includes(t))
    );
  }, [meetings, selectedTags]);

  // Group filtered meetings by date
  const groupedMeetings = useMemo(() => {
    return groupMeetingsByDate(filteredMeetings);
  }, [filteredMeetings]);

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

  const handleTagToggle = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatTime = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), 'h:mm a');
    } catch {
      return '';
    }
  };

  if (meetings.length === 0) {
    return (
      <Card className="p-6">
        <p className="text-center text-gray-400">No meetings recorded yet</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tag Filter */}
      <div className="flex items-center justify-between">
        <TagFilter
          availableTags={availableTags}
          selectedTags={selectedTags}
          onTagToggle={handleTagToggle}
        />
        <div className="text-sm text-gray-400">
          {filteredMeetings.length} meeting{filteredMeetings.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Grouped Meetings */}
      {groupedMeetings.map((group) => (
        <div key={group.label}>
          {/* Date Group Header */}
          <div className="flex items-center gap-3 mb-3">
            <span className="text-sm font-medium text-gray-400">{group.label}</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          {/* Meetings in this group */}
          <div className="space-y-2">
            {group.meetings.map((meeting) => {
              const isExpanded = expandedMeetingId === meeting.id;
              const isAnalyzing = analyzingId === meeting.id;

              return (
                <div
                  key={meeting.id}
                  className="group bg-[#1a1a1a] rounded-xl p-4 hover:bg-[#222] transition-colors border border-white/5"
                >
                  <div className="flex items-start justify-between">
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => onMeetingClick?.(meeting.id)}
                    >
                      {/* Title */}
                      <h3 className="text-white font-medium mb-1 hover:text-[#FFD100] transition-colors">
                        {meeting.title}
                      </h3>

                      {/* Time and metadata */}
                      <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                        <span>{formatTime(meeting.date)}</span>
                        {meeting.duration > 0 && (
                          <>
                            <span>•</span>
                            <span>{formatDuration(meeting.duration)}</span>
                          </>
                        )}
                      </div>

                      {/* Description/excerpt */}
                      {meeting.transcript && (
                        <p className="mt-2 text-sm text-gray-400 line-clamp-2">
                          {meeting.transcript.substring(0, 150)}
                          {meeting.transcript.length > 150 ? '...' : ''}
                        </p>
                      )}

                      {/* Speakers */}
                      {meeting.speakers && meeting.speakers.length > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          {meeting.speakers.slice(0, 4).map((speaker, idx) => (
                            <span
                              key={idx}
                              className="text-xs px-2 py-0.5 bg-white/5 rounded-full text-gray-400"
                            >
                              {speaker}
                            </span>
                          ))}
                          {meeting.speakers.length > 4 && (
                            <span className="text-xs text-gray-500">
                              +{meeting.speakers.length - 4} more
                            </span>
                          )}
                        </div>
                      )}

                      {/* Tags */}
                      {meeting.tags && meeting.tags.length > 0 && (
                        <div className="flex items-center gap-1.5 mt-2">
                          {meeting.tags.map((tag) => (
                            <Badge
                              key={tag}
                              variant="outline"
                              className="text-xs bg-[#2774AE]/10 border-[#2774AE]/30 text-[#FFD100]"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExpand(meeting.id);
                        }}
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-white"
                      >
                        {isExpanded ? 'Less' : 'More'}
                      </Button>
                      <button className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400">
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-white/10 space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-300 mb-2">Transcript</h4>
                        <div className="p-3 bg-white/5 rounded-lg max-h-[200px] overflow-y-auto">
                          <p className="text-sm text-gray-400 whitespace-pre-wrap">
                            {meeting.transcript || 'No transcript available'}
                          </p>
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-medium text-gray-300">
                            Next Steps & Action Items
                          </h4>
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
                          <div className="p-3 bg-[#2774AE]/10 rounded-lg border border-[#2774AE]/20">
                            <p className="text-sm text-gray-300 whitespace-pre-wrap">
                              {meeting.nextSteps}
                            </p>
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 italic">
                            Click "Analyze with AI" to generate action items
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {filteredMeetings.length === 0 && selectedTags.length > 0 && (
        <div className="text-center py-12">
          <Tag className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No meetings match the selected tags</p>
          <button
            onClick={() => setSelectedTags([])}
            className="mt-2 text-[#FFD100] hover:text-[#FFD100]/80 text-sm"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}
