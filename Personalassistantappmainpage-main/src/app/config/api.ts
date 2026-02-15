/**
 * API Configuration
 * 
 * Configures the frontend to connect to either the local Python API
 * or fall back to Supabase cloud functions.
 */

// Local API server (Python FastAPI)
export const LOCAL_API_URL = 'http://localhost:8000';

// Supabase fallback (for cloud deployment)
export const SUPABASE_PROJECT_ID = 'izohlncurobgfriyjiyp';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml6b2hsbmN1cm9iZ2ZyaXlqaXlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczODU0MjgsImV4cCI6MjA4Mjk2MTQyOH0.AgoYG5W7VIOErMJR9HIgfmmDGgrSw0-yi714wQMWgXk';

// Use local API by default
export const USE_LOCAL_API = true;

// Get the base URL for API calls
export function getApiUrl(path: string): string {
    if (USE_LOCAL_API) {
        return `${LOCAL_API_URL}${path}`;
    }
    return `https://${SUPABASE_PROJECT_ID}.supabase.co/functions/v1/make-server-7ea82c69${path}`;
}

// Get headers for API calls
export function getApiHeaders(): HeadersInit {
    if (USE_LOCAL_API) {
        return {
            'Content-Type': 'application/json',
        };
    }
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
    };
}

// WebSocket URL for live updates
export function getWebSocketUrl(): string {
    return 'ws://localhost:8000/ws';
}
