import React, { useEffect, useState } from 'react';
import { type TelemetryData, telemetryService } from '../services/websocket';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import TeleopPad from '../components/control/TeleopPad';
import LiveMapViewer from '../components/map/LiveMapViewer';

const Dashboard: React.FC = () => {
    const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
    const [history, setHistory] = useState<TelemetryData[]>([]);

    // V2 Options state
    const [selectedRobot, setSelectedRobot] = useState<string>('tb3_01');
    const [isAutoMode, setIsAutoMode] = useState<boolean>(false);

    useEffect(() => {
        telemetryService.connect();

        telemetryService.onMessage((data) => {
            // Ideally backend will emit `robot_id` in TelemetryData so we filter here
            // e.g. if (data.robot_id !== selectedRobot) return;
            setTelemetry(data);
            setHistory(prev => {
                const newHistory = [...prev, data];
                if (newHistory.length > 30) newHistory.shift();
                return newHistory;
            });
        });

        return () => {
            telemetryService.disconnect();
        };
    }, [selectedRobot]);

    const handleStop = () => {
        telemetryService.sendCommand('E_STOP', {});
        // Also stop velocities if teleop is active
        telemetryService.sendTwistCommand(selectedRobot, { linear_x_cmd: 0, angular_z_cmd: 0 });
    };

    const handleModeSwitch = () => {
        setIsAutoMode(prev => {
            const newMode = !prev;
            telemetryService.sendCommand('MODE_SWITCH', { mode: newMode ? 'AUTO' : 'MANUAL' });
            return newMode;
        });
    };

    return (
        <div style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h1>Live Telemetry Dashboard</h1>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                    Robot ID:{' '}
                    <select
                        value={selectedRobot}
                        onChange={(e) => setSelectedRobot(e.target.value)}
                        style={{ padding: '0.5rem', fontSize: '1.1rem', borderRadius: '4px' }}
                    >
                        <option value="tb3_01">tb3_01</option>
                        <option value="tb3_02">tb3_02</option>
                        <option value="scout_mini">scout_mini</option>
                    </select>
                </div>
            </div>

            {!telemetry ? (
                <p>Waiting for WebSocket connection...</p>
            ) : (
                <>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginTop: '1rem' }}>
                        <div className="card" style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                            <h3 style={{ borderBottom: '2px solid #0056b3', paddingBottom: '0.5rem', marginTop: 0 }}>Robot Pose</h3>
                            <p><strong>X:</strong> {telemetry.pose.x.toFixed(2)} m</p>
                            <p><strong>Y:</strong> {telemetry.pose.y.toFixed(2)} m</p>
                            <p><strong>Heading:</strong> {telemetry.pose.theta.toFixed(2)} rad</p>
                        </div>

                        <div className="card" style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                            <h3 style={{ borderBottom: '2px solid #0056b3', paddingBottom: '0.5rem', marginTop: 0 }}>System Status</h3>
                            <p><strong>Battery:</strong> {telemetry.battery.toFixed(1)}%</p>
                            <p><strong>State:</strong> <span style={{ color: telemetry.status === 'ERROR' ? 'red' : 'green', fontWeight: 'bold' }}>{telemetry.status}</span></p>
                        </div>

                        <div className="card" style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                            <h3 style={{ borderBottom: '2px solid #0056b3', paddingBottom: '0.5rem', marginTop: 0 }}>Command & Control</h3>
                            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                                <button onClick={handleStop} style={{ background: '#dc3545', color: 'white', padding: '0.75rem 1.5rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1.1rem', flex: 1 }}>E-STOP</button>
                                <button onClick={handleModeSwitch} style={{ background: isAutoMode ? '#198754' : '#0d6efd', color: 'white', padding: '0.75rem 1.5rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1.1rem', flex: 1 }}>
                                    {isAutoMode ? "Auto Mode" : "Manual Mode"}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Navigation Area */}
                    <div style={{ marginTop: '3rem', padding: '2rem', background: 'white', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.05)' }}>
                        <h2 style={{ textAlign: 'center', marginBottom: '2rem', color: '#444' }}>Navigation Interface</h2>
                        {isAutoMode ? (
                            <LiveMapViewer robotId={selectedRobot} telemetry={telemetry} />
                        ) : (
                            <TeleopPad robotId={selectedRobot} disabled={isAutoMode} />
                        )}
                    </div>

                    <div style={{ marginTop: '3rem', height: '300px' }}>
                        <h3>Live Battery Drain</h3>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={history}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="timestamp" tickFormatter={(time) => new Date(time).toLocaleTimeString()} />
                                <YAxis domain={[0, 100]} />
                                <Tooltip labelFormatter={(label) => new Date(label).toLocaleTimeString()} />
                                <Line type="monotone" dataKey="battery" stroke="#0056b3" strokeWidth={2} dot={false} isAnimationActive={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </>
            )}
        </div>
    );
};

export default Dashboard;
