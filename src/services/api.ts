// src/services/api.ts

export interface Session {
    id: string;
    alias: string;
    durationMinutes: number;
    distanceKm: number;
    startTime: string;
}

/**
 * Mock REST API Service
 * Person B (Backend) will replace this with real FastAPI endpoints.
 */
class ApiService {
    async getSessions(): Promise<Session[]> {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve([
                    { id: 'sess-001', alias: 'ms-2023-10-25-alpha', durationMinutes: 105, distanceKm: 3.2, startTime: '2023-10-25T14:00:00Z' },
                    { id: 'sess-002', alias: 'ms-2023-10-24-beta', durationMinutes: 45, distanceKm: 1.1, startTime: '2023-10-24T09:30:00Z' },
                ]);
            }, 500);
        });
    }

    async getSessionTelemetry(_sessionId: string): Promise<any[]> {
        // Return mock timeseries data for the chosen session
        return new Promise((resolve) => {
            setTimeout(() => {
                const data = [];
                let battery = 100;
                let ms = Date.now() - 3600000; // 1 hour ago
                for (let i = 0; i < 60; i++) {
                    ms += 60000;
                    battery -= Math.random();
                    data.push({ timestamp: ms, battery: battery });
                }
                resolve(data);
            }, 500);
        });
    }
}

export const apiService = new ApiService();
