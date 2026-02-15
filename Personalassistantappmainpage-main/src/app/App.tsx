import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { RecordingInterface } from './components/RecordingInterface';
import { MeetingHistory } from './components/MeetingHistory';
import { MeetingDetailView } from './components/MeetingDetailView';
import { PeopleView } from './components/PeopleView';
import { JournalInterface } from './components/JournalInterface';
import { SettingsPanel } from './components/SettingsPanel';
import { CalendarEventsPanel } from './components/CalendarEventsPanel';
import { Mic, History, BookOpen, Settings, Loader2, Users, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { getApiUrl, getApiHeaders, LOCAL_API_URL } from './config/api';

interface Meeting {
  id: string;
  title: string;
  date: string;
  speakers: string[];
  transcript: string;
  nextSteps: string;
  duration: number;
}

interface JournalEntry {
  id: string;
  date: string;
  entry: string;
  aiSuggestions: string;
}

export default function App() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>([]);
  const [isLoadingMeetings, setIsLoadingMeetings] = useState(true);
  const [isLoadingJournal, setIsLoadingJournal] = useState(true);
  const [activeTab, setActiveTab] = useState('record');
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);

  useEffect(() => {
    loadMeetings();
    loadJournalEntries();
  }, []);

  const loadMeetings = async () => {
    setIsLoadingMeetings(true);
    try {
      const response = await fetch(
        getApiUrl('/api/meetings'),
        {
          headers: getApiHeaders(),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMeetings(data.meetings);
      } else {
        console.error('Failed to load meetings:', await response.text());
      }
    } catch (error) {
      console.error('Error loading meetings:', error);
      toast.error('Failed to load meetings');
    } finally {
      setIsLoadingMeetings(false);
    }
  };

  const loadJournalEntries = async () => {
    setIsLoadingJournal(true);
    try {
      const response = await fetch(
        getApiUrl('/api/journal'),
        {
          headers: getApiHeaders(),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setJournalEntries(data.entries);
      } else {
        console.error('Failed to load journal entries:', await response.text());
      }
    } catch (error) {
      console.error('Error loading journal entries:', error);
      toast.error('Failed to load journal entries');
    } finally {
      setIsLoadingJournal(false);
    }
  };

  const handleSaveRecording = async (data: {
    title: string;
    speakers: string[];
    transcript: string;
    duration: number;
  }) => {
    try {
      const response = await fetch(
        getApiUrl('/api/meetings'),
        {
          method: 'POST',
          headers: getApiHeaders(),
          body: JSON.stringify(data),
        }
      );

      if (response.ok) {
        const result = await response.json();
        setMeetings([result.meeting, ...meetings]);
        toast.success('Meeting saved successfully!');
      } else {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save meeting');
      }
    } catch (error) {
      console.error('Error saving recording:', error);
      toast.error('Failed to save meeting');
      throw error;
    }
  };

  const handleAnalyzeMeeting = async (meetingId: string) => {
    try {
      const response = await fetch(
        getApiUrl(`/api/meetings/${meetingId}/analyze`),
        {
          method: 'PUT',
          headers: getApiHeaders(),
        }
      );

      if (response.ok) {
        const result = await response.json();
        setMeetings(meetings.map(m => m.id === meetingId ? result.meeting : m));
        toast.success('Meeting analyzed successfully!');
      } else {
        const error = await response.json();
        if (error.error === 'LLM API key not configured' || error.error === 'LLM provider not configured') {
          toast.error('Please configure your LLM provider and API key in Settings');
        } else {
          throw new Error(error.error || 'Failed to analyze meeting');
        }
      }
    } catch (error) {
      console.error('Error analyzing meeting:', error);
      toast.error('Failed to analyze meeting');
      throw error;
    }
  };

  const handleCreateJournalEntry = async (entry: string) => {
    try {
      const response = await fetch(
        getApiUrl('/api/journal'),
        {
          method: 'POST',
          headers: getApiHeaders(),
          body: JSON.stringify({ entry }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        setJournalEntries([result.journalEntry, ...journalEntries]);
        toast.success('Journal entry saved!');
      } else {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create journal entry');
      }
    } catch (error) {
      console.error('Error creating journal entry:', error);
      toast.error('Failed to save journal entry');
      throw error;
    }
  };

  const handleOptimizeJournalEntry = async (entryId: string) => {
    try {
      const response = await fetch(
        getApiUrl(`/api/journal/${entryId}/optimize`),
        {
          method: 'PUT',
          headers: getApiHeaders(),
        }
      );

      if (response.ok) {
        const result = await response.json();
        setJournalEntries(journalEntries.map(e => e.id === entryId ? result.journalEntry : e));
        toast.success('AI suggestions generated!');
      } else {
        const error = await response.json();
        if (error.error === 'LLM API key not configured' || error.error === 'LLM provider not configured') {
          toast.error('Please configure your LLM provider and API key in Settings');
        } else {
          throw new Error(error.error || 'Failed to optimize entry');
        }
      }
    } catch (error) {
      console.error('Error optimizing journal entry:', error);
      toast.error('Failed to generate suggestions');
      throw error;
    }
  };

  return (
    <div className="min-h-screen bg-[#111] dark">
      <Toaster />

      <div className="container max-w-6xl mx-auto p-6">
        <header className="mb-8">
          <h1 className="mb-2">Personal Assistant</h1>
          <p className="text-gray-400">
            Record meetings, track your journey, and get AI-powered insights
          </p>
        </header>

        <Tabs defaultValue="record" className="w-full" onValueChange={setActiveTab}>
          <TabsList className="w-full flex mb-6">
            <TabsTrigger value="record" className="gap-2 flex-1">
              <Mic className="w-4 h-4" />
              {activeTab === 'record' && 'Record'}
            </TabsTrigger>
            <TabsTrigger value="meetings" className="gap-2 flex-1">
              <History className="w-4 h-4" />
              {activeTab === 'meetings' && 'Meetings'}
            </TabsTrigger>
            <TabsTrigger value="calendar" className="gap-2 flex-1">
              <Calendar className="w-4 h-4" />
              {activeTab === 'calendar' && 'Calendar'}
            </TabsTrigger>
            <TabsTrigger value="journal" className="gap-2 flex-1">
              <BookOpen className="w-4 h-4" />
              {activeTab === 'journal' && 'Journal'}
            </TabsTrigger>
            <TabsTrigger value="people" className="gap-2 flex-1">
              <Users className="w-4 h-4" />
              {activeTab === 'people' && 'People'}
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2 flex-1">
              <Settings className="w-4 h-4" />
              {activeTab === 'settings' && 'Settings'}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="record">
            <RecordingInterface onRecordingComplete={() => {
              loadMeetings();
              setActiveTab('meetings');
            }} />
          </TabsContent>

          <TabsContent value="meetings">
            {selectedMeetingId ? (
              <MeetingDetailView
                meetingId={selectedMeetingId}
                onBack={() => setSelectedMeetingId(null)}
              />
            ) : (
              <>
                <div className="mb-4">
                  <h2>Meeting History</h2>
                  <p className="text-sm text-gray-400">
                    View all your recorded meetings with speakers, timestamps, and AI-generated next steps
                  </p>
                </div>
                {isLoadingMeetings ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                  </div>
                ) : (
                  <MeetingHistory
                    meetings={meetings}
                    onAnalyzeMeeting={handleAnalyzeMeeting}
                    onMeetingClick={(id) => setSelectedMeetingId(id)}
                  />
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="calendar">
            <CalendarEventsPanel />
          </TabsContent>

          <TabsContent value="journal">
            {isLoadingJournal ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <JournalInterface
                entries={journalEntries}
                onCreateEntry={handleCreateJournalEntry}
                onOptimizeEntry={handleOptimizeJournalEntry}
              />
            )}
          </TabsContent>

          <TabsContent value="people">
            <PeopleView />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}