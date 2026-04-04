/** HTTP API origin (no trailing slash). Override at build time: VITE_API_BASE_URL */
export function getApiBaseUrl(): string {
    const raw = import.meta.env.VITE_API_BASE_URL;
    if (typeof raw === 'string' && raw.trim()) {
        return raw.trim().replace(/\/$/, '');
    }
    return 'http://localhost:8000';
}

/** WebSocket URL for the dashboard ↔ backend `/ws/frontend` path */
export function getFrontendWebSocketUrl(): string {
    const base = getApiBaseUrl();
    const wsOrigin = base.replace(/^http/, 'ws');
    return `${wsOrigin}/ws/frontend`;
}
