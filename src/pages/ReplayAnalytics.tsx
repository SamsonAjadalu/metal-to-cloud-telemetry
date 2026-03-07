import React, { useEffect, useState } from 'react';
import { apiService, type Session } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const ReplayAnalytics: React.FC = () => {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [selectedSession, setSelectedSession] = useState<string | null>(null);
    const [replayData, setReplayData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiService.getSessions().then(data => {
            setSessions(data);
            setLoading(false);
        });
    }, []);

    const handleReplay = (sessionId: string) => {
        setLoading(true);
        setSelectedSession(sessionId);
        apiService.getSessionTelemetry(sessionId).then(data => {
            setReplayData(data);
            setLoading(false);
        });
    };

    return (
        <div style={{ padding: '2rem' }}>
            <h1>Missions Replay & Analytics</h1>
            <p>Select a historical session to view telemetry playback and statistics.</p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem', marginTop: '2rem' }}>
                <div className="card" style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                    <h3 style={{ marginTop: 0 }}>Available Sessions</h3>
                    {loading && !selectedSession ? <p>Loading sessions...</p> : (
                        <ul style={{ listStyleType: 'none', padding: 0 }}>
                            {sessions.map(s => (
                                <li key={s.id} style={{ padding: '1rem', border: '1px solid #eee', marginBottom: '1rem', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: selectedSession === s.id ? '#f0f8ff' : 'white' }}>
                                    <div>
                                        <strong>{s.alias}</strong>
                                        <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: '#666' }}>
                                            Duration: {s.durationMinutes}m | Distance: {s.distanceKm}km
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => handleReplay(s.id)}
                                        style={{ background: '#28a745', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                                    >
                                        Replay
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="card" style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                    <h3 style={{ marginTop: 0 }}>Replay Viewer</h3>
                    {!selectedSession ? (
                        <p style={{ color: '#666', fontStyle: 'italic' }}>Select a session from the list to view its replay data.</p>
                    ) : loading ? (
                        <p>Loading session data...</p>
                    ) : (
                        <div style={{ height: '400px', marginTop: '2rem' }}>
                            <h4>Historical Battery Performance</h4>
                            <ResponsiveContainer width="100%" height="80%">
                                <LineChart data={replayData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="timestamp" tickFormatter={(time) => new Date(time).toLocaleTimeString()} />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip labelFormatter={(label) => new Date(label).toLocaleTimeString()} />
                                    <Line type="monotone" dataKey="battery" stroke="#28a745" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ReplayAnalytics;
