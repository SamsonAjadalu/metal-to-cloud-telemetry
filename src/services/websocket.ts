// src/services/websocket.ts

export interface TelemetryData {
    timestamp: number;
    pose: { x: number; y: number; theta: number };
    battery: number;
    status: 'IDLE' | 'MOVING' | 'ERROR';
    map_id?: string;
    velocity?: { linear_x: number; angular_z: number };
}

/**
 * Mock WebSocket Service for Telemetry
 * Person B (Backend) will replace this with real FastAPI WebSocket connection.
 */
class TelemetryWebSocket {
    private url: string;
    private socket: WebSocket | null = null;
    private onMessageCallback: ((data: TelemetryData) => void) | null = null;

    constructor(url: string = 'ws://localhost:8000/ws/frontend') {
        this.url = url;
    }

    connect() {
        console.log(`[WebSocket] Connecting to ${this.url}...`);
        if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
            return;
        }
        
        this.socket = new WebSocket(this.url);
        
        this.socket.onopen = () => {
            console.log('[WebSocket] Connected');
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (this.onMessageCallback) {
                    this.onMessageCallback(data);
                }
            } catch (e) {
                console.error('[WebSocket] Error parsing message', e);
            }
        };

        this.socket.onclose = () => {
            console.log('[WebSocket] Disconnected');
            // Auto-reconnect could be implemented here
        };
    }

    disconnect() {
        console.log(`[WebSocket] Disconnecting...`);
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    onMessage(callback: (data: TelemetryData) => void) {
        this.onMessageCallback = callback;
    }

    sendCommand(command: string, payload: any) {
        console.log(`[WebSocket] Sending command: ${command}`, payload);
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type: 'sys_command', command, ...payload }));
        }
    }

    sendTwistCommand(robotId: string, twist: { linear_x_cmd: number, angular_z_cmd: number }) {
        console.log(`[WebSocket] Sending Twist -> Robot: ${robotId}`, twist);
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ 
                type: 'command', 
                robot_id: robotId, 
                linear_x_cmd: twist.linear_x_cmd,
                angular_z_cmd: twist.angular_z_cmd 
            }));
        }
    }

    sendGoalCommand(robotId: string, goal: { x: number, y: number, yaw: number }) {
        console.log(`[WebSocket] Sending Nav2 Goal -> Robot: ${robotId}`, goal);
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ 
                type: 'goal', 
                robot_id: robotId, 
                x: goal.x,
                y: goal.y,
                yaw: goal.yaw
            }));
        }
    }
}

export const telemetryService = new TelemetryWebSocket();
