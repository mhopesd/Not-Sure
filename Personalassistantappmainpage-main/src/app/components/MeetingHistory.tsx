import { useState, useMemo, useEffect, useCallback } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Loader2, Calendar, Clock, Users, Sparkles, Tag, MoreHorizontal, Search } from 'lucide-react';
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
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);

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

  // Debounced search
  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await fetch(
          `http://localhost:8000/api/meetings/search?q=${encodeURIComponent(searchQuery)}`
        );
        if (response.ok) {
          const data = await response.json();
          setSearchResults(data.results);
        }
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

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
      {/* Search + Tag Filter */}
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search meetings, transcripts, summaries..."
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#2774AE] transition-colors text-sm"
          />
          {isSearching && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#2774AE] animate-spin" />
          )}
        </div>

        <div className="flex items-center justify-between">
          <TagFilter
            availableTags={availableTags}
            selectedTags={selectedTags}
            onTagToggle={handleTagToggle}
          />
          <div className="text-sm text-gray-400">
            {searchResults ? `${searchResults.length} result${searchResults.length !== 1 ? 's' : ''}` : `${filteredMeetings.length} meeting${filteredMeetings.length !== 1 ? 's' : ''}`}
          </div>
        </div>
      </div>

      {/* Search Results */}
      {searchResults && searchResults.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Search Results</h3>
          {searchResults.map((result: any) => (
            <div
              key={result.meeting_id}
              onClick={() => onMeetingClick?.(result.meeting_id)}
              className="p-4 bg-white/5 hover:bg-white/10 rounded-lg cursor-pointer transition-colors border border-white/5"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white font-medium">{result.title}</h4>
                <span className="text-xs text-gray-500">{result.date}</span>
              </div>
              {result.matches.map((match: any, idx: number) => (
                <div key={idx} className="text-sm mb-1">
                  <span className="text-xs text-[#FFD100] uppercase mr-2">{match.field}</span>
                  <span className="text-gray-400">{match.snippet}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {searchResults && searchResults.length === 0 && searchQuery.length >= 2 && (
        <div className="text-center py-8 text-gray-500">
          No results found for "{searchQuery}"
        </div>
      )}

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
