// src/services/websocket.ts

export interface TelemetryData {
    timestamp: number;
    pose: { x: number; y: number; theta: number };
    battery: number;
    status: 'IDLE' | 'MOVING' | 'ERROR';
}

/**
 * Mock WebSocket Service for Telemetry
 * Person B (Backend) will replace this with real FastAPI WebSocket connection.
 */
class TelemetryWebSocket {
    private url: string;
    private socket: WebSocket | null = null;
    private onMessageCallback: ((data: TelemetryData) => void) | null = null;
    private mockInterval: number | ReturnType<typeof setInterval> | null = null;

    constructor(url: string = 'ws://localhost:8000/ws/telemetry') {
        this.url = url;
    }

    connect() {
        console.log(`[WebSocket] Connecting to ${this.url}...`);
        // Mocking the connection for now
        this.startMockStream();
    }

    disconnect() {
        console.log(`[WebSocket] Disconnecting...`);
        if (this.mockInterval) clearInterval(this.mockInterval);
        if (this.socket) this.socket.close();
    }

    onMessage(callback: (data: TelemetryData) => void) {
        this.onMessageCallback = callback;
    }

    sendCommand(command: string, payload: any) {
        console.log(`[WebSocket] Sending command: ${command}`, payload);
        // Real implementation will use this.socket.send()
    }

    private startMockStream() {
        let x = 0;
        let battery = 100;
        this.mockInterval = setInterval(() => {
            if (this.onMessageCallback) {
                x += 0.1;
                battery = Math.max(0, battery - 0.5);
                this.onMessageCallback({
                    timestamp: Date.now(),
                    pose: { x: parseFloat(x.toFixed(2)), y: 0, theta: 0 },
                    battery: battery,
                    status: battery > 20 ? 'MOVING' : 'IDLE',
                });
            }
        }, 1000);
    }
}

export const telemetryService = new TelemetryWebSocket();
