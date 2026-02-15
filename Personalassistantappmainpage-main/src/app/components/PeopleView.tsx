import { useState, useEffect, useMemo } from 'react';
import { Search, MoreHorizontal, Calendar, Mail, Users, ArrowUpDown } from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';
import { format, parseISO } from 'date-fns';

interface Person {
    name: string;
    email?: string;
    lastMeeting?: string;
    meetingCount: number;
    meetings: string[]; // Array of meeting IDs or titles
}

interface PeopleViewProps {
    onPersonClick?: (person: Person) => void;
}

// Generate consistent color based on name
function getAvatarColor(name: string): string {
    const colors = [
        'bg-[#2774AE]',
        'bg-blue-500',
        'bg-green-500',
        'bg-yellow-500',
        'bg-red-500',
        'bg-pink-500',
        'bg-indigo-500',
        'bg-teal-500',
        'bg-orange-500',
        'bg-cyan-500',
    ];

    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
}

function getInitial(name: string): string {
    return name.charAt(0).toUpperCase();
}

export function PeopleView({ onPersonClick }: PeopleViewProps) {
    const [people, setPeople] = useState<Person[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortField, setSortField] = useState<'name' | 'lastMeeting' | 'meetingCount'>('meetingCount');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

    useEffect(() => {
        fetchPeople();
    }, []);

    const fetchPeople = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(getApiUrl('/api/people'), {
                headers: getApiHeaders()
            });
            if (!response.ok) throw new Error('Failed to fetch people');
            const data = await response.json();

            // Transform API response to Person interface
            const peopleData: Person[] = data.people?.map((p: any) => ({
                name: p.name || 'Unknown',
                email: p.email || '',
                lastMeeting: p.last_meeting || p.lastMeeting || '',
                meetingCount: p.meeting_count || p.meetingCount || 0,
                meetings: p.meetings || []
            })) || [];

            setPeople(peopleData);
        } catch (error) {
            console.error('Error fetching people:', error);
        } finally {
            setIsLoading(false);
        }
    };

    // Filter and sort people
    const filteredPeople = useMemo(() => {
        let result = people;

        // Apply search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            result = result.filter(p =>
                p.name.toLowerCase().includes(query) ||
                (p.email && p.email.toLowerCase().includes(query))
            );
        }

        // Apply sorting
        result.sort((a, b) => {
            let comparison = 0;

            switch (sortField) {
                case 'name':
                    comparison = a.name.localeCompare(b.name);
                    break;
                case 'lastMeeting':
                    comparison = (a.lastMeeting || '').localeCompare(b.lastMeeting || '');
                    break;
                case 'meetingCount':
                    comparison = a.meetingCount - b.meetingCount;
                    break;
            }

            return sortDirection === 'asc' ? comparison : -comparison;
        });

        return result;
    }, [people, searchQuery, sortField, sortDirection]);

    const handleSort = (field: 'name' | 'lastMeeting' | 'meetingCount') => {
        if (sortField === field) {
            setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const formatDate = (dateStr: string) => {
        if (!dateStr) return '-';
        try {
            const date = parseISO(dateStr);
            return format(date, 'MMM d, yyyy \'at\' h:mm a');
        } catch {
            return dateStr;
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="w-8 h-8 border-2 border-[#2774AE] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="h-full">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white mb-2">People</h1>
                <p className="text-sm text-gray-400">
                    View all speakers and contacts from your meetings
                </p>
            </div>

            {/* Toolbar */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg text-sm text-gray-400 hover:bg-white/10 transition-colors">
                        <Calendar className="w-4 h-4" />
                        Last meeting
                    </button>
                </div>

                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search"
                        className="pl-9 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#2774AE] w-64"
                    />
                </div>
            </div>

            {/* Table */}
            <div className="bg-[#1a1a1a] rounded-xl border border-white/10 overflow-hidden">
                {/* Table Header */}
                <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-white/10 text-sm text-gray-400">
                    <button
                        onClick={() => handleSort('name')}
                        className="col-span-4 flex items-center gap-1 hover:text-white transition-colors text-left"
                    >
                        Name
                        <ArrowUpDown className="w-3.5 h-3.5" />
                    </button>
                    <div className="col-span-3">Email</div>
                    <button
                        onClick={() => handleSort('lastMeeting')}
                        className="col-span-3 flex items-center gap-1 hover:text-white transition-colors text-left"
                    >
                        Last meeting
                        <ArrowUpDown className="w-3.5 h-3.5" />
                    </button>
                    <button
                        onClick={() => handleSort('meetingCount')}
                        className="col-span-1 flex items-center gap-1 hover:text-white transition-colors text-left"
                    >
                        Meetings
                        <ArrowUpDown className="w-3.5 h-3.5" />
                    </button>
                    <div className="col-span-1"></div>
                </div>

                {/* Table Body */}
                {filteredPeople.length === 0 ? (
                    <div className="px-4 py-12 text-center">
                        <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-400">
                            {searchQuery ? 'No people match your search' : 'No people found in meetings'}
                        </p>
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {filteredPeople.map((person, idx) => (
                            <div
                                key={`${person.name}-${idx}`}
                                className="grid grid-cols-12 gap-4 px-4 py-3 items-center hover:bg-white/5 transition-colors cursor-pointer"
                                onClick={() => onPersonClick?.(person)}
                            >
                                {/* Name with avatar */}
                                <div className="col-span-4 flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-full ${getAvatarColor(person.name)} flex items-center justify-center text-white text-sm font-medium`}>
                                        {getInitial(person.name)}
                                    </div>
                                    <span className="text-white font-medium truncate">{person.name}</span>
                                </div>

                                {/* Email */}
                                <div className="col-span-3 text-gray-400 text-sm truncate">
                                    {person.email || '-'}
                                </div>

                                {/* Last meeting */}
                                <div className="col-span-3 text-gray-400 text-sm">
                                    {formatDate(person.lastMeeting || '')}
                                </div>

                                {/* Meeting count */}
                                <div className="col-span-1 text-white font-medium text-center">
                                    {person.meetingCount}
                                </div>

                                {/* Actions */}
                                <div className="col-span-1 flex justify-end">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            // TODO: Open action menu
                                        }}
                                        className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                                    >
                                        <MoreHorizontal className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Summary */}
            <div className="mt-4 text-sm text-gray-500">
                {filteredPeople.length} {filteredPeople.length === 1 ? 'person' : 'people'}
                {searchQuery && ` matching "${searchQuery}"`}
            </div>
        </div>
    );
}
