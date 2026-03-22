// src/services/api.ts

export interface Session {
    id: string;
    alias: string;
    durationMinutes: number;
    distanceKm: number;
    startTime: string;
}

export interface RobotInfo {
    robot_id: string;
    status: string;
    battery: number;
    x: number;
    y: number;
    total_distance_m: number;
    last_seen: string | null;
    last_seen_ago_s: number | null;
}

/**
 * REST API Service for backend endpoints.
 */
class ApiService {
    async getSessions(): Promise<Session[]> {
        try {
            const res = await fetch('http://localhost:8000/api/sessions');
            if (res.ok) {
                return await res.json();
            }
        } catch (err) {
            console.warn('[ApiService] Backend API not available for getSessions, falling back to mock.');
        }

        return new Promise((resolve) => {
            setTimeout(() => {
                resolve([
                    { id: 'sess-001', alias: 'ms-2023-10-25-alpha', durationMinutes: 105, distanceKm: 3.2, startTime: '2023-10-25T14:00:00Z' },
                    { id: 'sess-002', alias: 'ms-2023-10-24-beta', durationMinutes: 45, distanceKm: 1.1, startTime: '2023-10-24T09:30:00Z' },
                ]);
            }, 500);
        });
    }

    async getSessionTelemetry(sessionId: string): Promise<any[]> {
        try {
            const res = await fetch(`http://localhost:8000/api/sessions/${sessionId}/telemetry`);
            if (res.ok) {
                return await res.json();
            }
        } catch (err) {
            console.warn(`[ApiService] Backend API not available for getSessionTelemetry(${sessionId}), falling back to mock.`);
        }

        // Return mock timeseries data for the chosen session
        return new Promise((resolve) => {
            setTimeout(() => {
                const data = [];
                let battery = 100;
                let ms = Date.now() - 3600000; // 1 hour ago

                let x = 0;
                let y = 0;
                let yaw = 0;

                for (let i = 0; i < 60; i++) {
                    ms += 60000;
                    battery -= Math.random();

                    // Simulate some basic circular/wavy movement
                    x += Math.cos(yaw) * 0.5;
                    y += Math.sin(yaw) * 0.5;
                    yaw += 0.1;

                    data.push({ timestamp: ms, battery: battery, x: parseFloat(x.toFixed(2)), y: parseFloat(y.toFixed(2)), yaw: parseFloat(yaw.toFixed(2)) });
                }
                resolve(data);
            }, 500);
        });
    }

    async getFleet(): Promise<RobotInfo[]> {
        try {
            const res = await fetch('http://localhost:8000/api/fleet');
            if (res.ok) {
                return await res.json();
            }
        } catch (err) {
            console.warn('[ApiService] Backend API not available for getFleet.');
        }
        return [];
    }
}

export const apiService = new ApiService();
