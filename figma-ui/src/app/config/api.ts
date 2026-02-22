/**
 * API Configuration
 *
 * Configures the frontend to connect to the local Python FastAPI backend.
 */

// Local API server (Python FastAPI)
export const LOCAL_API_URL = 'http://localhost:8000';

// Get the base URL for API calls
export function getApiUrl(path: string): string {
    return `${LOCAL_API_URL}${path}`;
}

// Get headers for API calls
export function getApiHeaders(): HeadersInit {
    return {
        'Content-Type': 'application/json',
    };
}

// WebSocket URL for live updates
export function getWebSocketUrl(): string {
    return 'ws://localhost:8000/ws';
}
