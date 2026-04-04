import React, { useCallback, useEffect, useState } from 'react';
import { apiService, type RobotInfo } from '../services/api';

const FleetStoredSummary: React.FC = () => {
    const [fleet, setFleet] = useState<RobotInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(() => {
        setError(null);
        apiService
            .getFleet()
            .then((rows) => {
                setFleet(rows);
                setLoading(false);
            })
            .catch(() => {
                setError('Could not load fleet data from the API.');
                setLoading(false);
            });
    }, []);

    useEffect(() => {
        refresh();
        const interval = setInterval(refresh, 5000);
        return () => clearInterval(interval);
    }, [refresh]);

    const fmtTime = (iso: string | null) => {
        if (!iso) return '—';
        try {
            return new Date(iso).toLocaleString();
        } catch {
            return iso;
        }
    };

    return (
        <div style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ marginTop: 0 }}>Stored fleet summary</h1>
                    <p style={{ maxWidth: '640px', color: '#555', margin: 0 }}>
                        Rows below come from <code>GET /api/fleet</code> (PostgreSQL). Distance and last-seen persist across API restarts; this view is for demonstrating storage, not live replay.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={() => {
                        setLoading(true);
                        refresh();
                    }}
                    style={{ padding: '0.5rem 1rem', borderRadius: '4px', border: '1px solid #ccc', background: '#f8f9fa', cursor: 'pointer' }}
                >
                    Refresh now
                </button>
            </div>

            {error && <p style={{ color: '#b00020' }}>{error}</p>}
            {loading && fleet.length === 0 && !error && <p>Loading…</p>}

            <div className="card" style={{ padding: '0', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 4px 6px rgba(0,0,0,0.06)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
                    <thead>
                        <tr style={{ background: '#f5f5f5', textAlign: 'left' }}>
                            <th style={{ padding: '0.75rem 1rem' }}>Robot</th>
                            <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                            <th style={{ padding: '0.75rem 1rem' }}>Battery</th>
                            <th style={{ padding: '0.75rem 1rem' }}>Last position (x, y)</th>
                            <th style={{ padding: '0.75rem 1rem' }}>Distance (m)</th>
                            <th style={{ padding: '0.75rem 1rem' }}>Last seen</th>
                            <th style={{ padding: '0.75rem 1rem' }}>Seconds ago</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fleet.length === 0 && !loading ? (
                            <tr>
                                <td colSpan={7} style={{ padding: '1.5rem', color: '#666' }}>
                                    No robots in the database yet. Run the bridge so the backend can record fleet rows.
                                </td>
                            </tr>
                        ) : (
                            fleet.map((r) => (
                                <tr key={r.robot_id} style={{ borderTop: '1px solid #eee' }}>
                                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{r.robot_id}</td>
                                    <td style={{ padding: '0.75rem 1rem' }}>{r.status}</td>
                                    <td style={{ padding: '0.75rem 1rem' }}>{r.battery}</td>
                                    <td style={{ padding: '0.75rem 1rem' }}>
                                        ({r.x}, {r.y})
                                    </td>
                                    <td style={{ padding: '0.75rem 1rem' }}>{r.total_distance_m}</td>
                                    <td style={{ padding: '0.75rem 1rem' }}>{fmtTime(r.last_seen)}</td>
                                    <td style={{ padding: '0.75rem 1rem' }}>
                                        {r.last_seen_ago_s != null ? r.last_seen_ago_s : '—'}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default FleetStoredSummary;
