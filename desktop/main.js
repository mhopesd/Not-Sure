const { app, BrowserWindow, shell, dialog } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

// Keep references to prevent GC
let mainWindow = null;
let pythonProcess = null;

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
    // Fallback: hardcoded project path (set at build time)
    return '/Users/micha/audio-summary-app';
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

// ── App Lifecycle ──────────────────────────────────────────────────

app.whenReady().then(async () => {
    // Start the Python backend
    startBackend();

    // Create a splash/loading state
    createWindow();

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
    stopBackend();
    app.quit();
});

app.on('before-quit', () => {
    stopBackend();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
