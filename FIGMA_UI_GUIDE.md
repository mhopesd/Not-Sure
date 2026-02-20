# NotSure UI Overview — Figma Design Guide

This document provides a complete overview of the NotSure application's user interface to help you design a cohesive, consistent, and beautiful experience in Figma.

## App Architecture & Context
NotSure is a **macOS Desktop Application** (built with Electron) that helps users record, transcribe, and summarize their meetings. It consists of two main visual surfaces:
1. **The Native macOS Menu Bar Tray:** A persistent, quick-access dropdown from the top right of the mac screen.
2. **The Main App Window:** A rich, full-featured dashboard where users manage their recordings, view insights, and configure settings.

### Design Principles
- **Modern & Premium:** The app should feel native to macOS but feature a polished, modern aesthetic (think Apple Notes meets a high-end productivity app like Notion or Linear).
- **Unobtrusive:** During a meeting, the app should stay out of the way. The menu bar tray is the primary interaction point while recording. 
- **Dark Mode First:** By default, the app uses a dark theme. Colors should be vibrant against dark backgrounds (e.g., UCLA Blue `#2774AE` and Gold `#FFD100` are currently used).
- **Consistent Components:** Across all views, there should be a unified design system for inputs, buttons, cards, tags, and typography.

---

## 1. The Menu Bar Tray (Quick Access)
This is a small, vertical popover window that appears when clicking the NotSure icon in the macOS menu bar (top right).

**Key States & Interactions:**
*   **Idle State:** 
    *   Large, prominent "Start Recording" button.
    *   Quick glance at recent meetings (list of 2-3 recent items).
    *   Button to "Open Dashboard".
*   **Active Recording State:**
    *   Pulsing recording indicator (red dot or animated wave).
    *   Call duration timer.
    *   "Stop Recording" and "Pause" controls.
    *   Live audio visualizer (VU meter).
    *   Scrolling ticker of the live transcript.

---

## 2. The Main Dashboard (Full Application)

The main application window is a single-page reacting interface divided into several core "Views" or "Pages". Navigation typically happens via a sidebar or top navigation bar.

### A. The Setup / Onboarding Wizard (`OnboardingWizard.tsx`)
A smooth, elegant multi-step flow for first-time users to set up the app.
*   **Steps include:**
    1.  **Welcome Screen:** Value proposition and "Get Started" button.
    2.  **Permissions:** Requesting Microphone and System Audio (BlackHole) access. Needs clear visual feedback for granted/denied states.
    3.  **LLM Configuration:** Choosing between Cloud AI (Gemini) or Local AI (Ollama). Requires API key input toggles.
    4.  **Integrations:** Connecting Google/Microsoft calendars.
*   **Design Needs:** Progress indicators, clean typography for instructions, clear success/error states for connections.

### B. The Recording Interface (`RecordingInterface.tsx`)
The view shown inside the main app when a recording is active or about to start.
*   **Key Elements:**
    *   **Audio Input Selection:** Dropdowns or toggles to select Microphone, System Audio, or both (`MicrophoneSelector.tsx`).
    *   **Main Controls:** Massive, clear Start/Stop/Pause buttons.
    *   **Live Status:** Audio visualizer, recording timer.
    *   **Live Intelligence:** As the meeting happens, a split-pane or side-panel showing:
        *   The live, scrolling transcript.
        *   Real-time AI insights (e.g., auto-detected Action Items or Decisions popping up).

### C. The Processing/Loading View (`ProcessingProgress.tsx`)
The transition state after hitting "Stop Recording" while the AI generates the summary.
*   **Key Elements:**
    *   Progress bar or circular spinner.
    *   Status text indicating the current step (e.g., "Transcribing...", "Analyzing...", "Generating Tasks...").
    *   Ideally, a dynamic or engaging animation so the user doesn't get bored.

### D. The Meeting Detail View (`MeetingDetailView.tsx`)
The deepest, most content-rich view. This is where users consume the results of a specific meeting.
*   **Layout:** Often a split view or heavily structured scrollable page.
*   **Core Components:**
    *   **Header:** Meeting Title (editable), Date, Time, Duration, and Meeting Type tags.
    *   **Audio Player:** Playback controls for the original audio file with a waveform scrubber.
    *   **AI Summary Section:** High-level summary text.
    *   **Action Items & Decisions:** Checkboxes for action items, highlighted blocks for key decisions.
    *   **Full Transcript:** Searchable, scrollable list of text blocks. Ideally with speaker timelines or diarization (e.g., "Speaker 1", "Speaker 2").
    *   **Metadata Sidebar:** Tags, related people (`PeopleView.tsx`), integration links.

### E. The Library / Meeting History (`MeetingHistory.tsx`)
The archive of all past recordings.
*   **Key Elements:**
    *   **Search Bar:** Prominent global search.
    *   **Filters (`TagFilter.tsx`):** Filter by tags (e.g., #client, #internal), meeting type, dates, or specific people.
    *   **List/Grid of Cards:** Each past meeting is a card showing Title, Date, Duration, and a brief snippet of the summary or key action items.

### F. Journal / Reflection (`JournalInterface.tsx`)
A space where users can reflect on their day, pulling in data from their meetings.
*   **Key Elements:**
    *   Rich text editor or simple text area for writing notes.
    *   A prompt area where the AI can suggest reflections based on the day's meetings.
    *   A timeline view of past journal entries.

### G. Settings & Integrations (`SettingsPanel.tsx`, `IntegrationsPanel.tsx`, `CalendarEventsPanel.tsx`)
Administrative interfaces for configuring the app.
*   **Key Elements:**
    *   **General Settings:** Toggles for dark/light mode, default models, transcript formatting.
    *   **Integrations:** Cards for Google/Microsoft with "Connect" / "Disconnect" states and status indicators.
    *   **Upcoming Events:** A widget showing the next few meetings synced from the calendar.

---

## 3. Global UI Components to Define
To ensure consistency, please design a master component library (Design System) containing:

1.  **Typography Scale:** Headers, body text, small labels, timestamp fonts (monospace).
2.  **Color Palette:** Backgrounds (dark and light variants), Primary Brand colors, semantic colors (Success green, Error red, Warning yellow), text colors.
3.  **Buttons:** Primary, Secondary, Tertiary/Ghost, Icon-only. (Default, Hover, Disabled states).
4.  **Inputs:** Text fields, dropdown selects, toggles/switches, checkboxes.
5.  **Cards & Containers:** Elevated surfaces, border radii, drop shadows.
6.  **Tags/Pills:** For categorizing meetings and labeling UI states.
7.  **Data Visualizations:** Audio waveforms, processing progress bars, level meters.

**Final Note to Designer:** The goal is to make capturing meeting information feel effortless and reviewing it feel like having a superpower. Focus on clarity, reducing visual clutter, and drawing attention to the most important elements (Action Items and pending tasks).
