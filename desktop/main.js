const { app, BrowserWindow, Tray, Menu, nativeImage, Notification, shell, dialog } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

// Keep references to prevent GC
let mainWindow = null;
let pythonProcess = null;
let tray = null;

// Tray state
let isRecording = false;
let lastActionCount = 0;
let lastDecisionCount = 0;
let trayPollInterval = null;

const BACKEND_PORT = 8000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
const IS_DEV = !app.isPackaged;

/**
 * Resolve the path to the project root.
 * - In dev: the parent of the desktop/ folder
 * - In packaged: reads from a .project_root file or uses the parent of the .app's Contents dir
 */
function getProjectRoot() {
    if (IS_DEV) {
        return path.resolve(__dirname, '..');
    }
    // Packaged: check for a .project_root config file next to the .app
    const configPath = path.join(path.dirname(app.getPath('exe')), '..', '..', '..', '.project_root');
    if (fs.existsSync(configPath)) {
        return fs.readFileSync(configPath, 'utf-8').trim();
    }
    // Fallback: resolve from the .app bundle's parent directory
    // In macOS .app bundles: exe is at NotSure.app/Contents/MacOS/NotSure
    const appDir = path.join(path.dirname(app.getPath('exe')), '..', '..', '..');
    const resolved = path.resolve(appDir);
    if (fs.existsSync(path.join(resolved, 'venv')) || fs.existsSync(path.join(resolved, 'api_server.py'))) {
        return resolved;
    }
    // Last resort: check home directory
    const homeFallback = path.join(app.getPath('home'), 'Not-Sure');
    if (fs.existsSync(homeFallback)) {
        return homeFallback;
    }
    console.error('Could not determine project root. Create a .project_root file next to the .app bundle.');
    return resolved;
}

/**
 * Resolve the Python executable from the project venv.
 */
function getPythonPath() {
    const root = getProjectRoot();
    const venvPython = path.join(root, 'venv', 'bin', 'python');
    if (fs.existsSync(venvPython)) {
        return venvPython;
    }
    // Fallback: system python
    return 'python3';
}

/**
 * Start the FastAPI backend as a child process.
 */
function startBackend() {
    const pythonPath = getPythonPath();
    const projectRoot = getProjectRoot();
    const serverScript = path.join(projectRoot, 'api_server.py');

    console.log(`[Electron] Starting backend: ${pythonPath} ${serverScript}`);
    console.log(`[Electron] Working directory: ${projectRoot}`);

    pythonProcess = spawn(pythonPath, [serverScript], {
        cwd: projectRoot,
        env: {
            ...process.env,
            PYTHONUNBUFFERED: '1',
        },
        stdio: ['ignore', 'pipe', 'pipe'],
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`[Backend] ${data.toString().trim()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`[Backend] ${data.toString().trim()}`);
    });

    pythonProcess.on('error', (err) => {
        console.error('[Electron] Failed to start backend:', err);
        dialog.showErrorBox(
            'Backend Error',
            `Failed to start the Python backend.\n\n${err.message}\n\nMake sure the Python virtual environment exists at:\n${path.join(projectRoot, 'venv')}`
        );
    });

    pythonProcess.on('exit', (code, signal) => {
        console.log(`[Electron] Backend exited with code ${code}, signal ${signal}`);
        pythonProcess = null;
    });
}

/**
 * Wait for the backend to become ready by polling the health endpoint.
 */
function waitForBackend(maxAttempts = 30, intervalMs = 500) {
    return new Promise((resolve, reject) => {
        let attempts = 0;

        const check = () => {
            attempts++;
            const req = http.get(`${BACKEND_URL}/`, (res) => {
                if (res.statusCode === 200) {
                    resolve();
                } else if (attempts < maxAttempts) {
                    setTimeout(check, intervalMs);
                } else {
                    reject(new Error('Backend did not respond with 200'));
                }
            });

            req.on('error', () => {
                if (attempts < maxAttempts) {
                    setTimeout(check, intervalMs);
                } else {
                    reject(new Error('Backend did not start in time'));
                }
            });

            req.setTimeout(1000, () => {
                req.destroy();
                if (attempts < maxAttempts) {
                    setTimeout(check, intervalMs);
                } else {
                    reject(new Error('Backend connection timed out'));
                }
            });
        };

        check();
    });
}

/**
 * Stop the Python backend gracefully.
 */
function stopBackend() {
    if (pythonProcess) {
        console.log('[Electron] Stopping backend...');
        pythonProcess.kill('SIGTERM');

        // Force kill after 3 seconds
        setTimeout(() => {
            if (pythonProcess) {
                pythonProcess.kill('SIGKILL');
                pythonProcess = null;
            }
        }, 3000);
    }
}

/**
 * Create the main application window.
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 860,
        minWidth: 900,
        minHeight: 600,
        titleBarStyle: 'hiddenInset',
        trafficLightPosition: { x: 16, y: 16 },
        backgroundColor: '#111111',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
        show: false,
    });

    // Determine what to load
    if (IS_DEV) {
        // Dev mode: load from Vite dev server
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    } else {
        // Production: load the built frontend
        const frontendPath = path.join(__dirname, 'frontend', 'index.html');
        mainWindow.loadFile(frontendPath);
    }

    // Show window once ready (avoids white flash)
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Open external links in system browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('http://localhost')) {
            return { action: 'allow' }; // OAuth popups
        }
        shell.openExternal(url);
        return { action: 'deny' };
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// ── Tray (Menu Bar) ───────────────────────────────────────────────

/**
 * Simple HTTP GET helper that returns parsed JSON.
 */
function apiGet(endpoint) {
    return new Promise((resolve, reject) => {
        const req = http.get(`${BACKEND_URL}${endpoint}`, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch { reject(new Error('Bad JSON')); }
            });
        });
        req.on('error', reject);
        req.setTimeout(3000, () => { req.destroy(); reject(new Error('Timeout')); });
    });
}

/**
 * Simple HTTP POST helper.
 */
function apiPost(endpoint, body = {}) {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify(body);
        const url = new URL(`${BACKEND_URL}${endpoint}`);
        const req = http.request({
            hostname: url.hostname,
            port: url.port,
            path: url.pathname,
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) },
        }, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch { resolve({}); }
            });
        });
        req.on('error', reject);
        req.setTimeout(10000, () => { req.destroy(); reject(new Error('Timeout')); });
        req.write(payload);
        req.end();
    });
}

/**
 * Format seconds as M:SS.
 */
function formatDuration(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * Send a macOS notification.
 */
function sendNotification(title, body, subtitle = '') {
    if (Notification.isSupported()) {
        const n = new Notification({ title, body, subtitle, silent: true });
        n.show();
    }
}

/**
 * Toggle recording on/off.
 */
async function toggleRecording() {
    try {
        if (isRecording) {
            await apiPost('/api/recordings/stop');
            isRecording = false;
            lastActionCount = 0;
            lastDecisionCount = 0;
            sendNotification('Recording Saved', 'Transcript and summary are being generated.');
        } else {
            await apiPost('/api/recordings/start');
            isRecording = true;
            lastActionCount = 0;
            lastDecisionCount = 0;
            sendNotification('Recording Started', 'Your meeting is being recorded and analyzed.');
        }
        updateTrayMenu();
    } catch (err) {
        sendNotification('Error', err.message || 'Failed to toggle recording');
    }
}

/**
 * Build/rebuild the tray context menu.
 */
function updateTrayMenu(statusLine, insightItems) {
    if (!tray) return;

    const recordLabel = isRecording ? '⏹  Stop Recording' : '⏺  Start Recording';
    const statusLabel = statusLine || (isRecording ? '📊  Recording...' : '📊  Status: Idle');

    const menuTemplate = [
        { label: recordLabel, click: toggleRecording },
        { type: 'separator' },
        { label: statusLabel, enabled: false },
    ];

    // Add insights submenu if available
    if (insightItems && insightItems.length > 0) {
        menuTemplate.push({
            label: '💡  Live Insights',
            submenu: insightItems.map((item) => ({ label: item, enabled: false })),
        });
    }

    menuTemplate.push(
        { type: 'separator' },
        {
            label: '🖥  Open Dashboard',
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                    mainWindow.focus();
                } else {
                    createWindow();
                }
            },
        },
        { type: 'separator' },
        { label: 'Quit', click: () => app.quit() },
    );

    const contextMenu = Menu.buildFromTemplate(menuTemplate);
    tray.setContextMenu(contextMenu);
}

/**
 * Poll the backend for recording status and insights, update tray.
 */
async function pollBackend() {
    try {
        const status = await apiGet('/api/recordings/status');
        isRecording = status.is_recording || false;

        // Update tray title (shows next to icon in menu bar)
        if (isRecording) {
            const dur = formatDuration(status.duration || 0);
            const mt = status.meeting_type ? status.meeting_type.replace(/_/g, ' ') : '';
            const parts = [dur, mt, status.topic].filter(Boolean);
            tray.setTitle(` ${parts.join(' · ')}`);
        } else {
            tray.setTitle('');
        }

        // Build status line
        let statusLine;
        if (isRecording) {
            const parts = [formatDuration(status.duration || 0)];
            if (status.meeting_type) parts.push(status.meeting_type.replace(/_/g, ' '));
            if (status.topic) parts.push(status.topic);
            statusLine = `📊  Recording ${parts.join(' | ')}`;
        } else {
            statusLine = '📊  Status: Idle';
        }

        // Fetch insights during recording
        let insightItems = [];
        if (isRecording) {
            try {
                const insights = await apiGet('/api/recordings/insights');

                // Build submenu items
                const kp = insights.key_points || [];
                kp.slice(0, 5).forEach((p) => insightItems.push(`• ${p.slice(0, 60)}`));

                const actions = insights.action_items || [];
                if (actions.length > 0) {
                    insightItems.push('── Action Items ──');
                    actions.forEach((a) => {
                        let label = `☐ ${(a.text || '').slice(0, 50)}`;
                        if (a.assignee) label += ` → ${a.assignee}`;
                        insightItems.push(label);
                    });
                }

                const decisions = insights.decisions || [];
                if (decisions.length > 0) {
                    insightItems.push('── Decisions ──');
                    decisions.forEach((d) => insightItems.push(`✓ ${d.slice(0, 60)}`));
                }

                // Notify on NEW action items
                if (actions.length > lastActionCount && lastActionCount > 0) {
                    const newOnes = actions.slice(lastActionCount);
                    newOnes.forEach((a) => {
                        sendNotification(
                            '📋 Action Item',
                            a.text || 'New action item',
                            a.assignee ? `Assigned to ${a.assignee}` : ''
                        );
                    });
                }
                lastActionCount = actions.length;

                // Notify on NEW decisions
                if (decisions.length > lastDecisionCount && lastDecisionCount > 0) {
                    const newOnes = decisions.slice(lastDecisionCount);
                    newOnes.forEach((d) => {
                        sendNotification('⚡ Decision Made', d);
                    });
                }
                lastDecisionCount = decisions.length;

            } catch { /* insights not available yet */ }
        }

        updateTrayMenu(statusLine, insightItems);

    } catch {
        // Backend not reachable
        updateTrayMenu('📊  Status: Backend offline', []);
    }
}

// Meeting app detection state
let detectedMeetingApps = new Set();    // Currently running meeting apps
let dismissedApps = new Map();          // app → timestamp of dismissal (5 min cooldown)
let meetingDetectionInterval = null;

// Known meeting apps: process name → friendly label
const MEETING_APPS = {
    'zoom.us': 'Zoom',
    'Microsoft Teams': 'Microsoft Teams',
    'Webex': 'Webex',
    'FaceTime': 'FaceTime',
    'Slack': 'Slack',
    'Discord': 'Discord',
    'Skype': 'Skype',
    'GoTo Meeting': 'GoTo Meeting',
    'BlueJeans': 'BlueJeans',
    'Around': 'Around',
};

// Browser tab markers — if Chrome/Edge/Safari has a Meet/Teams tab we detect via audio
const BROWSER_MEETING_INDICATORS = [
    'Google Chrome Helper (Renderer)',  // Often active during Meet
];

/**
 * Get list of running macOS apps via `osascript`.
 * Returns an array of app names.
 */
function getRunningApps() {
    return new Promise((resolve) => {
        const { execFile } = require('child_process');
        execFile('osascript', ['-e', 'tell application "System Events" to get name of every process whose background only is false'], (err, stdout) => {
            if (err) {
                resolve([]);
                return;
            }
            const apps = stdout.trim().split(', ').map(a => a.trim());
            resolve(apps);
        });
    });
}

/**
 * Check if any meeting-related processes are using the microphone.
 * Uses macOS `lsof` on the audio device to detect active audio capture.
 */
function checkAudioCapture() {
    return new Promise((resolve) => {
        const { exec } = require('child_process');
        // Check for processes accessing CoreAudio
        exec("ps aux | grep -i 'coreaudiod\\|audioinput' | grep -v grep", (err, stdout) => {
            resolve(stdout || '');
        });
    });
}

/**
 * Scan for newly launched meeting apps and prompt the user.
 */
async function detectMeetingApps() {
    // Don't prompt if already recording
    if (isRecording) {
        detectedMeetingApps.clear();
        return;
    }

    try {
        const runningApps = await getRunningApps();
        const now = Date.now();
        const COOLDOWN_MS = 5 * 60 * 1000; // 5 minutes

        for (const [processName, friendlyName] of Object.entries(MEETING_APPS)) {
            const isRunning = runningApps.some(app =>
                app.toLowerCase().includes(processName.toLowerCase())
            );

            if (isRunning && !detectedMeetingApps.has(processName)) {
                // Check cooldown: don't re-prompt within 5 minutes of dismissal
                const dismissedAt = dismissedApps.get(processName);
                if (dismissedAt && (now - dismissedAt) < COOLDOWN_MS) {
                    continue;
                }

                // New meeting app detected!
                detectedMeetingApps.add(processName);
                console.log(`[Meeting Detection] Detected: ${friendlyName}`);

                // Show actionable notification
                promptRecording(friendlyName);
            } else if (!isRunning && detectedMeetingApps.has(processName)) {
                // App was closed — remove from tracked set
                detectedMeetingApps.delete(processName);
            }
        }
    } catch (err) {
        console.error('[Meeting Detection] Error:', err);
    }
}

/**
 * Show a notification asking if the user wants to start recording.
 * On click → start recording. On close → cooldown.
 */
function promptRecording(appName) {
    if (!Notification.isSupported()) return;

    const notification = new Notification({
        title: `${appName} Detected`,
        body: `It looks like you're joining a call. Tap to start recording.`,
        subtitle: 'Personal Assistant',
        silent: false,
        hasReply: false,
        actions: [{ type: 'button', text: 'Record' }],
        closeButtonText: 'Dismiss',
    });

    // User clicked the notification → start recording
    notification.on('click', async () => {
        if (!isRecording) {
            try {
                await apiPost('/api/recordings/start', { title: `${appName} Call` });
                isRecording = true;
                lastActionCount = 0;
                lastDecisionCount = 0;
                updateTrayMenu();
                sendNotification('Recording Started', `Recording your ${appName} call.`);
            } catch (err) {
                sendNotification('Error', err.message || 'Failed to start recording');
            }
        }
    });

    // User clicked the "Record" action button
    notification.on('action', async (event, index) => {
        if (!isRecording) {
            try {
                await apiPost('/api/recordings/start', { title: `${appName} Call` });
                isRecording = true;
                lastActionCount = 0;
                lastDecisionCount = 0;
                updateTrayMenu();
                sendNotification('Recording Started', `Recording your ${appName} call.`);
            } catch (err) {
                sendNotification('Error', err.message || 'Failed to start recording');
            }
        }
    });

    // User dismissed → set cooldown so we don't nag
    notification.on('close', () => {
        // Find which process name matches this app
        for (const [processName, name] of Object.entries(MEETING_APPS)) {
            if (name === appName) {
                dismissedApps.set(processName, Date.now());
                break;
            }
        }
    });

    notification.show();
}

/**
 * Start the meeting detection polling loop.
 */
function startMeetingDetection() {
    // Poll every 10 seconds for meeting apps
    meetingDetectionInterval = setInterval(detectMeetingApps, 10000);
    // Also run immediately
    detectMeetingApps();
}

/**
 * Create the system tray icon and menu.
 */
function createTray() {
    // Create a template image for the tray (mic icon)
    // Using a simple 16x16 emoji-based approach for macOS
    tray = new Tray(nativeImage.createEmpty());
    tray.setTitle('');
    tray.setToolTip('Personal Assistant');

    // Use the app icon resized for tray, or empty with title
    const iconPath = path.join(__dirname, 'icons', 'icon.png');
    if (fs.existsSync(iconPath)) {
        const icon = nativeImage.createFromPath(iconPath).resize({ width: 18, height: 18 });
        icon.setTemplateImage(true);
        tray.setImage(icon);
    }

    // Build initial menu
    updateTrayMenu();

    // Click to show/hide window
    tray.on('click', () => {
        if (mainWindow) {
            if (mainWindow.isVisible()) {
                mainWindow.hide();
            } else {
                mainWindow.show();
                mainWindow.focus();
            }
        } else {
            createWindow();
        }
    });

    // Start polling backend status + meeting detection
    trayPollInterval = setInterval(pollBackend, 5000);
    startMeetingDetection();
}

// ── App Lifecycle ──────────────────────────────────────────────────

app.whenReady().then(async () => {
    // Start the Python backend
    startBackend();

    // Create a splash/loading state
    createWindow();

    // Create the menu bar tray icon
    createTray();

    try {
        await waitForBackend();
        console.log('[Electron] Backend is ready!');

        // Reload the page now that the backend is up
        if (mainWindow) {
            if (IS_DEV) {
                mainWindow.loadURL('http://localhost:5173');
            } else {
                const frontendPath = path.join(__dirname, 'frontend', 'index.html');
                mainWindow.loadFile(frontendPath);
            }
        }
    } catch (err) {
        console.error('[Electron] Backend failed to start:', err);
        dialog.showErrorBox(
            'Startup Error',
            'The Python backend failed to start.\n\nPlease check:\n1. Python venv exists\n2. Ollama is installed\n3. Required packages are installed'
        );
    }
});

app.on('window-all-closed', () => {
    // On macOS, keep the app running in the tray when all windows are closed
    if (process.platform !== 'darwin') {
        stopBackend();
        app.quit();
    }
});

app.on('before-quit', () => {
    if (trayPollInterval) clearInterval(trayPollInterval);
    if (meetingDetectionInterval) clearInterval(meetingDetectionInterval);
    stopBackend();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

