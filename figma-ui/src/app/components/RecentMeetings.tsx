import { Clock, FileText, Users, ChevronRight } from "lucide-react";

interface Meeting {
  id: string;
  title: string;
  time: string;
  duration: string;
  participants: number;
  tag: string;
  tagColor: string;
}

const RECENT_MEETINGS: Meeting[] = [
  {
    id: "1",
    title: "Q3 Strategy Review",
    time: "Today, 2:00 PM",
    duration: "45 min",
    participants: 5,
    tag: "internal",
    tagColor: "#2774AE",
  },
  {
    id: "2",
    title: "Client Onboarding — Acme Corp",
    time: "Today, 11:30 AM",
    duration: "32 min",
    participants: 3,
    tag: "client",
    tagColor: "#FFD100",
  },
  {
    id: "3",
    title: "Design System Sync",
    time: "Yesterday, 4:15 PM",
    duration: "28 min",
    participants: 4,
    tag: "design",
    tagColor: "#6dd58c",
  },
];

export function RecentMeetings() {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between px-1 mb-2">
        <span className="text-[11px] text-white/40 uppercase tracking-wider">
          Recent Meetings
        </span>
        <span className="text-[10px] text-[#2774AE] cursor-pointer hover:text-[#3a8fd4] transition-colors">
          View All
        </span>
      </div>
      {RECENT_MEETINGS.map((meeting) => (
        <button
          key={meeting.id}
          className="w-full flex items-center gap-3 p-2.5 rounded-lg hover:bg-white/[0.06] transition-all duration-200 group text-left"
        >
          <div className="w-8 h-8 rounded-lg bg-white/[0.06] flex items-center justify-center shrink-0 group-hover:bg-white/[0.1] transition-colors">
            <FileText size={14} className="text-white/50" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[12px] text-white/90 truncate">
                {meeting.title}
              </span>
              <span
                className="text-[9px] px-1.5 py-[1px] rounded-full shrink-0"
                style={{
                  backgroundColor: `${meeting.tagColor}20`,
                  color: meeting.tagColor,
                }}
              >
                {meeting.tag}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-white/35 flex items-center gap-1">
                <Clock size={9} />
                {meeting.time}
              </span>
              <span className="text-[10px] text-white/25">·</span>
              <span className="text-[10px] text-white/35">{meeting.duration}</span>
              <span className="text-[10px] text-white/25">·</span>
              <span className="text-[10px] text-white/35 flex items-center gap-0.5">
                <Users size={9} />
                {meeting.participants}
              </span>
            </div>
          </div>
          <ChevronRight
            size={12}
            className="text-white/20 group-hover:text-white/40 transition-colors shrink-0"
          />
        </button>
      ))}
    </div>
  );
}
