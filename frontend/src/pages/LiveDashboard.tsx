import React, { useEffect, useState, useRef } from 'react';
import { type TelemetryData, telemetryService } from '../services/websocket';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import TeleopPad from '../components/control/TeleopPad';
import LiveMapViewer from '../components/map/LiveMapViewer';

const Dashboard: React.FC = () => {
    const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
    const [history, setHistory] = useState<TelemetryData[]>([]);

    const [isAutoMode, setIsAutoMode] = useState<boolean>(false);
    
    // Dynamic Robot ID Tracking
    const [activeRobots, setActiveRobots] = useState<string[]>([]);
    const [selectedRobot, setSelectedRobotState] = useState<string>('');
    const selectedRobotRef = useRef<string>('');

    const setSelectedRobot = (robotId: string) => {
        setSelectedRobotState(robotId);
        selectedRobotRef.current = robotId;
        // Clear history when switching robots — fresh start for the new robot
        setHistory([]);
        setTelemetry(null);
    };

    useEffect(() => {
        telemetryService.connect();

        telemetryService.onMessage((data) => {
            if (data.robot_id) {
                setActiveRobots(prev => {
                    if (!prev.includes(data.robot_id!)) {
                        if (selectedRobotRef.current === '') {
                            setSelectedRobot(data.robot_id!);
                        }
                        return [...prev, data.robot_id!].sort();
                    }
                    return prev;
                });
            }

            if (selectedRobotRef.current && data.robot_id !== selectedRobotRef.current) return;

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
    }, []);

    const handleStop = () => {
        telemetryService.sendCommand('E_STOP', {});
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
                        <option value="" disabled>Waiting for data...</option>
                        {activeRobots.map(id => (
                            <option key={id} value={id}>{id}</option>
                        ))}
                    </select>
                </div>
            </div>

            {!telemetry ? (
                <p>Waiting for WebSocket connection...</p>
            ) : (
                <>
                    {/* Top row: Telemetry cards */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginTop: '1rem' }}>
                        <div className="card" style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                            <h3 style={{ borderBottom: '2px solid #0056b3', paddingBottom: '0.5rem', marginTop: 0 }}>Robot Pose</h3>
                            <p><strong>X:</strong> {telemetry.x?.toFixed(2)} m</p>
                            <p><strong>Y:</strong> {telemetry.y?.toFixed(2)} m</p>
                            <p><strong>Heading:</strong> {telemetry.yaw?.toFixed(2)} rad</p>

                            <h3 style={{ borderBottom: '2px solid #0056b3', paddingBottom: '0.5rem', marginTop: '1rem' }}>Velocity</h3>
                            <p><strong>Linear:</strong> {telemetry.linear_x?.toFixed(2) ?? '0.00'} m/s</p>
                            <p><strong>Angular:</strong> {telemetry.angular_z?.toFixed(2) ?? '0.00'} rad/s</p>
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

                    {/* Main content: Map always visible + Controls side by side */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '2rem' }}>
                        {/* Left: Live Map — always visible, updates live with robot position */}
                        <div style={{ padding: '1.5rem', background: 'white', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.05)' }}>
                            <h2 style={{ textAlign: 'center', marginBottom: '1rem', marginTop: 0, color: '#444', fontSize: '1.3rem' }}>Live Map</h2>
                            <LiveMapViewer 
                                robotId={selectedRobot} 
                                telemetry={telemetry}
                                goalEnabled={isAutoMode}
                            />
                        </div>

                        {/* Right: Controls — switches between joystick and goal info */}
                        <div style={{ padding: '1.5rem', background: 'white', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                            <h2 style={{ textAlign: 'center', marginBottom: '1rem', marginTop: 0, color: '#444', fontSize: '1.3rem' }}>
                                {isAutoMode ? 'Autonomous Navigation' : 'Manual Control'}
                            </h2>
                            {isAutoMode ? (
                                <div style={{ textAlign: 'center', color: '#666' }}>
                                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎯</div>
                                    <p style={{ fontSize: '1.1rem', fontWeight: 500 }}>Click on the map to send a Nav2 Goal</p>
                                    <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', color: '#999' }}>
                                        The robot will autonomously navigate to the clicked position
                                    </p>
                                </div>
                            ) : (
                                <TeleopPad robotId={selectedRobot} disabled={isAutoMode} />
                            )}
                        </div>
                    </div>

                    {/* Battery chart */}
                    <div style={{ marginTop: '2rem', height: '250px' }}>
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
