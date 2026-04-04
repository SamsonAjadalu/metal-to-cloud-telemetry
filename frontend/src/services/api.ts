// src/services/api.ts

import { getApiBaseUrl } from '../config';

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

class ApiService {
    async getFleet(): Promise<RobotInfo[]> {
        const base = getApiBaseUrl();
        try {
            const res = await fetch(`${base}/api/fleet`);
            if (res.ok) {
                return await res.json();
            }
        } catch {
            console.warn('[ApiService] Backend API not available for getFleet.');
        }
        return [];
    }
}

export const apiService = new ApiService();
