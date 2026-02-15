import { useState, useEffect } from 'react';
import { ArrowLeft, Copy, Check, Plus, MoreHorizontal, Tag, Mail, Calendar, Send, X, Loader2 } from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';
import { toast } from 'sonner';

interface Meeting {
    id: string;
    title: string;
    date: string;
    duration: number | string;
    speakers: string[];
    transcript: string;
    executive_summary: string;
    highlights: string[];
    tasks: any[];
    tags: string[];
    start_time: string;
    end_time: string;
}

interface MeetingDetailViewProps {
    meetingId: string;
    onBack: () => void;
}

interface IntegrationProvider {
    connected: boolean;
    has_credentials: boolean;
    email: string | null;
}

type TabType = 'summary' | 'transcript' | 'tasks' | 'scratchpad';

export function MeetingDetailView({ meetingId, onBack }: MeetingDetailViewProps) {
    const [meeting, setMeeting] = useState<Meeting | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<TabType>('summary');
    const [scratchpad, setScratchpad] = useState('');
    const [copied, setCopied] = useState(false);

    // Integration state
    const [showShareDialog, setShowShareDialog] = useState(false);
    const [shareEmail, setShareEmail] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [isAddingToCalendar, setIsAddingToCalendar] = useState(false);
    const [integrationStatus, setIntegrationStatus] = useState<{
        microsoft: IntegrationProvider;
        google: IntegrationProvider;
    } | null>(null);

    useEffect(() => {
        fetchMeeting();
        fetchIntegrationStatus();
    }, [meetingId]);

    const fetchMeeting = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(getApiUrl(`/api/meetings/${meetingId}`), {
                headers: getApiHeaders()
            });
            if (!response.ok) throw new Error('Failed to fetch meeting');
            const data = await response.json();
            setMeeting(data);
        } catch (error) {
            console.error('Error fetching meeting:', error);
            toast?.error('Failed to load meeting details');
        } finally {
            setIsLoading(false);
        }
    };

    const fetchIntegrationStatus = async () => {
        try {
            const response = await fetch(getApiUrl('/api/integrations/status'), {
                headers: getApiHeaders()
            });
            if (response.ok) {
                setIntegrationStatus(await response.json());
            }
        } catch (error) {
            console.error('Error fetching integration status:', error);
        }
    };

    const connectedEmailProvider = integrationStatus
        ? integrationStatus.microsoft.connected ? 'microsoft'
            : integrationStatus.google.connected ? 'google'
                : null
        : null;

    const connectedCalendarProvider = connectedEmailProvider; // same providers

    const handleShareEmail = async () => {
        if (!meeting || !shareEmail.trim() || !connectedEmailProvider) return;

        setIsSending(true);
        try {
            const bodyHtml = `
                <h2>${meeting.title}</h2>
                <p><strong>Date:</strong> ${meeting.date}</p>
                ${meeting.speakers?.length ? `<p><strong>Speakers:</strong> ${meeting.speakers.join(', ')}</p>` : ''}
                <h3>Executive Summary</h3>
                <p>${meeting.executive_summary || 'No summary available'}</p>
                ${meeting.highlights?.length ? `
                    <h3>Key Highlights</h3>
                    <ul>${meeting.highlights.map(h => `<li>${h}</li>`).join('')}</ul>
                ` : ''}
                ${meeting.tasks?.length ? `
                    <h3>Action Items</h3>
                    <ul>${meeting.tasks.map(t => `<li>${typeof t === 'string' ? t : t.text || t.task || t.action_item || ''}</li>`).join('')}</ul>
                ` : ''}
            `;

            const response = await fetch(getApiUrl('/api/integrations/email/send'), {
                method: 'POST',
                headers: { ...getApiHeaders(), 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: connectedEmailProvider,
                    to: shareEmail,
                    subject: `Meeting Summary: ${meeting.title}`,
                    body_html: bodyHtml,
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to send');
            }

            toast?.success('Meeting summary sent!');
            setShowShareDialog(false);
            setShareEmail('');
        } catch (error: any) {
            toast?.error(error.message || 'Failed to send email');
        } finally {
            setIsSending(false);
        }
    };

    const handleAddToCalendar = async () => {
        if (!meeting || !connectedCalendarProvider) return;

        setIsAddingToCalendar(true);
        try {
            const startDate = meeting.start_time
                ? new Date(`${meeting.date}T${meeting.start_time}`)
                : new Date(meeting.date);
            const endDate = meeting.end_time
                ? new Date(`${meeting.date}T${meeting.end_time}`)
                : new Date(startDate.getTime() + 60 * 60 * 1000);

            const response = await fetch(getApiUrl('/api/integrations/calendar/events'), {
                method: 'POST',
                headers: { ...getApiHeaders(), 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: connectedCalendarProvider,
                    title: meeting.title,
                    start: startDate.toISOString(),
                    end: endDate.toISOString(),
                    description: meeting.executive_summary || '',
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to create event');
            }

            toast?.success('Event added to calendar!');
        } catch (error: any) {
            toast?.error(error.message || 'Failed to add to calendar');
        } finally {
            setIsAddingToCalendar(false);
        }
    };

    const copyToClipboard = async (text: string, type: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            toast?.success(`${type} copied to clipboard`);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            toast?.error('Failed to copy to clipboard');
        }
    };

    const formatTime = (dateStr: string) => {
        if (!dateStr) return '';
        try {
            const date = new Date(dateStr);
            return date.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
        } catch {
            return dateStr;
        }
    };

    const formatDate = (dateStr: string) => {
        if (!dateStr) return '';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
        } catch {
            return dateStr;
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (!meeting) {
        return (
            <div className="text-center py-20">
                <p className="text-gray-400">Meeting not found</p>
                <button onClick={onBack} className="mt-4 text-purple-400 hover:text-purple-300">
                    ← Back to meetings
                </button>
            </div>
        );
    }

    const tabs: { id: TabType; label: string }[] = [
        { id: 'summary', label: 'Summary' },
        { id: 'transcript', label: 'Transcript' },
        { id: 'tasks', label: 'Tasks' },
        { id: 'scratchpad', label: 'Scratchpad' },
    ];

    return (
        <div className="h-full">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
                <button onClick={onBack} className="hover:text-white flex items-center gap-1">
                    <ArrowLeft className="w-4 h-4" />
                    Meetings
                </button>
                <span>›</span>
                <span className="text-white">{meeting.title}</span>
            </div>

            {/* Header */}
            <div className="mb-6">
                <div className="flex items-start justify-between mb-4">
                    <h1 className="text-2xl font-bold text-white">{meeting.title}</h1>

                    {/* Action buttons */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => connectedEmailProvider ? setShowShareDialog(true) : toast?.error('Connect an email provider in Settings first')}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${connectedEmailProvider
                                    ? 'bg-blue-600/20 text-blue-400 hover:bg-blue-600/30'
                                    : 'bg-white/5 text-gray-500 hover:bg-white/10'
                                }`}
                            title={connectedEmailProvider ? 'Share meeting summary via email' : 'Connect an email provider in Settings'}
                        >
                            <Mail className="w-4 h-4" />
                            Share
                        </button>
                        <button
                            onClick={() => connectedCalendarProvider ? handleAddToCalendar() : toast?.error('Connect a calendar provider in Settings first')}
                            disabled={isAddingToCalendar}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${connectedCalendarProvider
                                    ? 'bg-purple-600/20 text-purple-400 hover:bg-purple-600/30'
                                    : 'bg-white/5 text-gray-500 hover:bg-white/10'
                                }`}
                            title={connectedCalendarProvider ? 'Add this meeting to your calendar' : 'Connect a calendar provider in Settings'}
                        >
                            {isAddingToCalendar ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calendar className="w-4 h-4" />}
                            Calendar
                        </button>
                    </div>
                </div>

                <div className="flex flex-wrap gap-6 text-sm">
                    <div className="flex items-center gap-2">
                        <span className="text-gray-400">Time</span>
                        <span className="text-white">
                            {formatDate(meeting.date)}, {meeting.start_time || formatTime(meeting.date)}
                            {meeting.end_time && ` - ${meeting.end_time}`}
                        </span>
                    </div>

                    {meeting.speakers && meeting.speakers.length > 0 && (
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">Speakers</span>
                            <span className="text-white">
                                {meeting.speakers.slice(0, 2).join(', ')}
                                {meeting.speakers.length > 2 && ` & ${meeting.speakers.length - 2} more`}
                            </span>
                        </div>
                    )}

                    <div className="flex items-center gap-2">
                        <span className="text-gray-400">Tags</span>
                        <button className="text-gray-400 hover:text-white flex items-center gap-1">
                            <Tag className="w-4 h-4" /> Add tag
                        </button>
                    </div>
                </div>
            </div>

            {/* Share Email Dialog */}
            {showShareDialog && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-[#1e1e1e] border border-white/10 rounded-xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Mail className="w-5 h-5 text-blue-400" />
                                Share Meeting Summary
                            </h3>
                            <button onClick={() => setShowShareDialog(false)} className="text-gray-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <p className="text-sm text-gray-400 mb-4">
                            Send the summary and action items for <span className="text-white">"{meeting.title}"</span> via {connectedEmailProvider === 'microsoft' ? 'Outlook' : 'Gmail'}.
                        </p>

                        <input
                            type="email"
                            value={shareEmail}
                            onChange={(e) => setShareEmail(e.target.value)}
                            placeholder="Recipient email address"
                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors mb-4"
                            autoFocus
                        />

                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setShowShareDialog(false)}
                                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleShareEmail}
                                disabled={isSending || !shareEmail.trim()}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white text-sm font-medium transition-colors"
                            >
                                {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                                Send
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-6 border-b border-white/10 mb-6">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`pb-3 transition-colors ${activeTab === tab.id
                            ? 'text-white border-b-2 border-purple-500 font-medium'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1">
                {/* Summary Tab */}
                {activeTab === 'summary' && (
                    <div>
                        <div className="flex items-center gap-4 mb-6">
                            <button className="text-sm text-gray-400 hover:text-white flex items-center gap-1">
                                ▼ Template
                            </button>
                            <button
                                onClick={() => copyToClipboard(meeting.executive_summary, 'Summary')}
                                className="text-sm text-gray-400 hover:text-white flex items-center gap-1"
                            >
                                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                Copy summary
                            </button>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-4">Executive Summary</h3>
                                {meeting.executive_summary ? (
                                    <p className="text-gray-300 leading-relaxed">{meeting.executive_summary}</p>
                                ) : (
                                    <p className="text-gray-500 italic">No summary available</p>
                                )}
                            </div>

                            {meeting.highlights && meeting.highlights.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-4">Key Highlights</h3>
                                    <ul className="space-y-3">
                                        {meeting.highlights.map((highlight, idx) => (
                                            <li key={idx} className="flex items-start gap-2 text-gray-300">
                                                <span className="text-purple-400 mt-1">•</span>
                                                <span>{highlight}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Transcript Tab */}
                {activeTab === 'transcript' && (
                    <div>
                        <div className="flex items-center gap-4 mb-6">
                            <button
                                onClick={() => copyToClipboard(meeting.transcript, 'Transcript')}
                                className="text-sm text-gray-400 hover:text-white flex items-center gap-1"
                            >
                                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                Copy transcript
                            </button>
                        </div>

                        {meeting.transcript ? (
                            <div className="prose prose-invert max-w-none">
                                <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                                    {meeting.transcript}
                                </p>
                            </div>
                        ) : (
                            <p className="text-gray-500 italic">No transcript available</p>
                        )}
                    </div>
                )}

                {/* Tasks Tab */}
                {activeTab === 'tasks' && (
                    <div>
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-4">
                                <span className="text-sm text-gray-400">Tasks</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-gray-400">Assignee</span>
                                    <span className="text-sm text-gray-400">All</span>
                                </div>
                            </div>
                            <button className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1">
                                <Plus className="w-4 h-4" /> Add Task
                            </button>
                        </div>

                        {meeting.tasks && meeting.tasks.length > 0 ? (
                            <div className="space-y-3">
                                {meeting.tasks.map((task, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-start gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={task.completed || false}
                                            onChange={() => { }}
                                            className="mt-1 w-4 h-4 rounded border-gray-600 bg-transparent text-purple-600 focus:ring-purple-500"
                                        />
                                        <div className="flex-1">
                                            <p className="text-gray-300">
                                                {typeof task === 'string' ? task : task.text || task.task || task.action_item || 'Task'}
                                            </p>
                                            {(task.assignee || task.speaker) && (
                                                <div className="flex items-center gap-2 mt-1">
                                                    <div className="w-5 h-5 rounded-full bg-purple-600 flex items-center justify-center text-xs text-white">
                                                        {(task.assignee || task.speaker || '?')[0].toUpperCase()}
                                                    </div>
                                                    <span className="text-sm text-gray-500">{task.assignee || task.speaker}</span>
                                                </div>
                                            )}
                                        </div>
                                        <button className="p-1 rounded hover:bg-white/10">
                                            <MoreHorizontal className="w-4 h-4 text-gray-400" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500 italic">No tasks extracted from this meeting</p>
                        )}
                    </div>
                )}

                {/* Scratchpad Tab */}
                {activeTab === 'scratchpad' && (
                    <div>
                        <textarea
                            value={scratchpad}
                            onChange={(e) => setScratchpad(e.target.value)}
                            placeholder="Write private notes..."
                            className="w-full h-64 bg-transparent border-none text-gray-300 placeholder-gray-500 focus:outline-none resize-none"
                        />
                    </div>
                )}
            </div>
        </div>
    );
}
