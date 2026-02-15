import { useState, useEffect, useCallback } from 'react';
import { Calendar, Clock, MapPin, ExternalLink, Loader2, RefreshCw, Settings2 } from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';
import { format, parseISO, isToday, isTomorrow, isThisWeek } from 'date-fns';

interface CalendarEvent {
    id: string;
    title: string;
    start: string;
    end: string;
    location?: string;
    description?: string;
    provider: string;
    link?: string;
}

interface IntegrationProvider {
    connected: boolean;
    has_credentials: boolean;
    email: string | null;
}

export function CalendarEventsPanel() {
    const [events, setEvents] = useState<CalendarEvent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [hasConnected, setHasConnected] = useState(false);
    const [daysAhead, setDaysAhead] = useState(7);

    const fetchEvents = useCallback(async (showRefresh = false) => {
        if (showRefresh) setIsRefreshing(true);
        else setIsLoading(true);

        try {
            // Check integration status first
            const statusRes = await fetch(getApiUrl('/api/integrations/status'), {
                headers: getApiHeaders(),
            });
            if (statusRes.ok) {
                const status = await statusRes.json();
                const anyConnected = status.microsoft?.connected || status.google?.connected;
                setHasConnected(anyConnected);

                if (!anyConnected) {
                    setEvents([]);
                    return;
                }
            }

            const response = await fetch(getApiUrl(`/api/integrations/calendar/events?days_ahead=${daysAhead}`), {
                headers: getApiHeaders(),
            });
            if (response.ok) {
                const data = await response.json();
                setEvents(data.events || []);
            }
        } catch (error) {
            console.error('Failed to fetch calendar events:', error);
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    }, [daysAhead]);

    useEffect(() => {
        fetchEvents();
    }, [fetchEvents]);

    const groupEventsByDay = (events: CalendarEvent[]) => {
        const groups: Record<string, CalendarEvent[]> = {};
        for (const event of events) {
            const date = event.start.split('T')[0];
            if (!groups[date]) groups[date] = [];
            groups[date].push(event);
        }
        return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
    };

    const formatDayLabel = (dateStr: string) => {
        try {
            const date = parseISO(dateStr);
            if (isToday(date)) return 'Today';
            if (isTomorrow(date)) return 'Tomorrow';
            return format(date, 'EEEE, MMM d');
        } catch {
            return dateStr;
        }
    };

    const formatEventTime = (start: string, end: string) => {
        try {
            const s = parseISO(start);
            const e = parseISO(end);
            return `${format(s, 'h:mm a')} – ${format(e, 'h:mm a')}`;
        } catch {
            return '';
        }
    };

    const providerIcon = (provider: string) => {
        return provider === 'microsoft' ? '🪟' : '🔵';
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
            </div>
        );
    }

    if (!hasConnected) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-purple-600/10 flex items-center justify-center mb-4">
                    <Calendar className="w-8 h-8 text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">No Calendar Connected</h3>
                <p className="text-gray-400 max-w-sm mb-6">
                    Connect your Microsoft or Google account in Settings to see your upcoming events here.
                </p>
                <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-lg text-sm text-gray-400">
                    <Settings2 className="w-4 h-4" />
                    Go to Settings → Service Integrations
                </div>
            </div>
        );
    }

    const grouped = groupEventsByDay(events);

    return (
        <div className="h-full">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Calendar</h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Upcoming events from your connected calendars
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <select
                        value={daysAhead}
                        onChange={(e) => setDaysAhead(Number(e.target.value))}
                        className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-purple-500"
                    >
                        <option value={3}>Next 3 days</option>
                        <option value={7}>Next 7 days</option>
                        <option value={14}>Next 14 days</option>
                        <option value={30}>Next 30 days</option>
                    </select>
                    <button
                        onClick={() => fetchEvents(true)}
                        disabled={isRefreshing}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {/* Events */}
            {events.length === 0 ? (
                <div className="text-center py-16">
                    <Calendar className="w-10 h-10 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">No upcoming events in the next {daysAhead} days</p>
                </div>
            ) : (
                <div className="space-y-6">
                    {grouped.map(([dateStr, dayEvents]) => (
                        <div key={dateStr}>
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                                {formatDayLabel(dateStr)}
                            </h3>
                            <div className="space-y-2">
                                {dayEvents.map((event) => (
                                    <div
                                        key={event.id}
                                        className="flex items-start gap-3 p-4 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 transition-colors group"
                                    >
                                        {/* Time bar */}
                                        <div className={`w-1 self-stretch rounded-full ${event.provider === 'microsoft' ? 'bg-blue-500' : 'bg-red-400'
                                            }`} />

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-2">
                                                <h4 className="font-medium text-white truncate">{event.title}</h4>
                                                <span className="text-xs shrink-0" title={event.provider}>
                                                    {providerIcon(event.provider)}
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-3 mt-1.5 text-sm text-gray-400">
                                                <div className="flex items-center gap-1">
                                                    <Clock className="w-3.5 h-3.5" />
                                                    {formatEventTime(event.start, event.end)}
                                                </div>
                                                {event.location && (
                                                    <div className="flex items-center gap-1 truncate">
                                                        <MapPin className="w-3.5 h-3.5 shrink-0" />
                                                        <span className="truncate">{event.location}</span>
                                                    </div>
                                                )}
                                            </div>

                                            {event.description && (
                                                <p className="text-sm text-gray-500 mt-2 line-clamp-2">{event.description}</p>
                                            )}
                                        </div>

                                        {event.link && (
                                            <a
                                                href={event.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-white/10 text-gray-400 transition-all"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
