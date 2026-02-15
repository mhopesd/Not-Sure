import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Card } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { RecordingInterface } from './components/RecordingInterface';
import { MeetingHistory } from './components/MeetingHistory';
import { JournalInterface } from './components/JournalInterface';
import { SettingsPanel } from './components/SettingsPanel';
import { Mic, History, BookOpen, Settings, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { projectId, publicAnonKey } from '../../utils/supabase/info';

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
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginProvider, setLoginProvider] = useState<'google' | 'microsoft' | 'sso' | null>(null);
  const [showEmailLogin, setShowEmailLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);

  useEffect(() => {
    if (isLoggedIn) {
      loadMeetings();
      loadJournalEntries();
    }
  }, [isLoggedIn]);

  const loadMeetings = async () => {
    setIsLoadingMeetings(true);
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/meetings`,
        {
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
          },
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
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/journal`,
        {
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
          },
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
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/meetings`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${publicAnonKey}`,
          },
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
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/meetings/${meetingId}/analyze`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
          },
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
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/journal`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${publicAnonKey}`,
          },
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
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/journal/${entryId}/optimize`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
          },
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

  const handleLogin = async (provider: 'google' | 'microsoft' | 'sso') => {
    setIsLoggingIn(true);
    setLoginProvider(provider);
    try {
      // Simulate login process
      await new Promise(resolve => setTimeout(resolve, 2500));
      
      toast.success(`Successfully logged in with ${provider.charAt(0).toUpperCase() + provider.slice(1)}`);
      setIsLoggedIn(true);
      
      // Load data after login
      loadMeetings();
      loadJournalEntries();
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Login failed. Please try again.');
    } finally {
      setIsLoggingIn(false);
      setLoginProvider(null);
    }
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please enter both email and password');
      return;
    }
    
    setIsLoggingIn(true);
    try {
      // Simulate email login/signup process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const action = isSignUp ? 'Account created' : 'Successfully logged in';
      toast.success(`${action}! Welcome to Personal Assistant`);
      setIsLoggedIn(true);
      
      // Load data after login
      loadMeetings();
      loadJournalEntries();
    } catch (error) {
      console.error('Email login error:', error);
      toast.error(isSignUp ? 'Sign up failed' : 'Login failed');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // If not logged in, show login screen
  if (!isLoggedIn) {
    // Show loading screen if currently logging in
    if (isLoggingIn && loginProvider) {
      const providerName = loginProvider === 'google' ? 'Google' : 
                          loginProvider === 'microsoft' ? 'Microsoft' : 'SSO';
      
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
          <Toaster />
          
          <div className="text-center">
            <div className="mb-6">
              <Loader2 className="w-16 h-16 animate-spin text-blue-600 mx-auto" />
            </div>
            
            <h2 className="mb-2">Signing you in...</h2>
            <p className="text-gray-600 mb-4">
              Authenticating with {providerName}
            </p>
            
            <div className="space-y-2 text-sm text-gray-500">
              <div className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>Verifying credentials</span>
              </div>
              <div className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-75" />
                <span>Establishing secure connection</span>
              </div>
              <div className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-150" />
                <span>Loading your workspace</span>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    // Show login form
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <Toaster />
        
        <Card className="w-full max-w-md p-8">
          <div className="text-center mb-8">
            <h1 className="mb-2">Personal Assistant</h1>
            <p className="text-gray-600">
              Sign in to access your meetings, journal, and AI insights
            </p>
          </div>

          {!showEmailLogin ? (
            <>
              <div className="space-y-4">
                <Button
                  onClick={() => handleLogin('google')}
                  disabled={isLoggingIn}
                  className="w-full gap-3"
                  size="lg"
                  variant="outline"
                >
                  {isLoggingIn && loginProvider === 'google' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="currentColor"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                  )}
                  Continue with Google
                </Button>

                <Button
                  onClick={() => handleLogin('microsoft')}
                  disabled={isLoggingIn}
                  className="w-full gap-3"
                  size="lg"
                  variant="outline"
                >
                  {isLoggingIn && loginProvider === 'microsoft' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zm12.6 0H12.6V0H24v11.4z" />
                    </svg>
                  )}
                  Continue with Microsoft
                </Button>

                <Button
                  onClick={() => handleLogin('sso')}
                  disabled={isLoggingIn}
                  className="w-full gap-3"
                  size="lg"
                  variant="outline"
                >
                  {isLoggingIn && loginProvider === 'sso' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  )}
                  Continue with SSO
                </Button>

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">Or</span>
                  </div>
                </div>

                <Button
                  onClick={() => setShowEmailLogin(true)}
                  className="w-full gap-3"
                  size="lg"
                  variant="outline"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                  Continue with Email
                </Button>
              </div>

              <p className="text-xs text-center text-gray-500 mt-6">
                By continuing, you agree to our Terms of Service and Privacy Policy
              </p>
            </>
          ) : (
            <>
              <form onSubmit={handleEmailLogin} className="space-y-4">
                <div>
                  <label className="text-sm mb-2 block">Email</label>
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoggingIn}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm mb-2 block">Password</label>
                  <Input
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoggingIn}
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={isLoggingIn}
                >
                  {isLoggingIn ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      {isSignUp ? 'Creating Account...' : 'Signing In...'}
                    </>
                  ) : (
                    isSignUp ? 'Create Account' : 'Sign In'
                  )}
                </Button>
              </form>

              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={() => setIsSignUp(!isSignUp)}
                  className="text-sm text-blue-600 hover:underline"
                  disabled={isLoggingIn}
                >
                  {isSignUp ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
                </button>
              </div>

              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setShowEmailLogin(false);
                    setEmail('');
                    setPassword('');
                    setIsSignUp(false);
                  }}
                  className="text-sm text-gray-600 hover:underline"
                  disabled={isLoggingIn}
                >
                  ← Back to all sign in options
                </button>
              </div>

              <p className="text-xs text-center text-gray-500 mt-6">
                By continuing, you agree to our Terms of Service and Privacy Policy
              </p>
            </>
          )}
        </Card>
      </div>
    );
  }

  // Main application (shown after login)
  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster />
      
      <div className="container max-w-6xl mx-auto p-6">
        <header className="mb-8">
          <h1 className="mb-2">Personal Assistant</h1>
          <p className="text-gray-600">
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
            <TabsTrigger value="journal" className="gap-2 flex-1">
              <BookOpen className="w-4 h-4" />
              {activeTab === 'journal' && 'Journal'}
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2 flex-1">
              <Settings className="w-4 h-4" />
              {activeTab === 'settings' && 'Settings'}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="record">
            <RecordingInterface onSaveRecording={handleSaveRecording} />
          </TabsContent>

          <TabsContent value="meetings">
            <div className="mb-4">
              <h2>Meeting History</h2>
              <p className="text-sm text-gray-600">
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
              />
            )}
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

          <TabsContent value="settings">
            <SettingsPanel projectId={projectId} publicAnonKey={publicAnonKey} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}