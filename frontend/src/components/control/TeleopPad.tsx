import React from 'react';
import { Joystick } from 'react-joystick-component';
import type { IJoystickUpdateEvent } from 'react-joystick-component/build/lib/Joystick';
import { telemetryService } from '../../services/websocket';

interface TeleopPadProps {
    robotId: string;
    disabled?: boolean;
}

const TeleopPad: React.FC<TeleopPadProps> = ({ robotId, disabled }) => {

    const handleMove = (event: IJoystickUpdateEvent) => {
        if (event.type === 'stop') {
            telemetryService.sendTwistCommand(robotId, { linear_x_cmd: 0, angular_z_cmd: 0 });
            return;
        }

        // Stick reports ~[-1, 1]; scale to m/s and rad/s at full deflection.
        const max_velocity = 0.22; // m/s (~TurtleBot3 Burger limit)
        const max_angular = 1.5; // rad/s

        const x_scaled = event.y !== null ? event.y * max_velocity : 0;
        const z_scaled = event.x !== null ? -event.x * max_angular : 0;

        telemetryService.sendTwistCommand(robotId, { linear_x_cmd: x_scaled, angular_z_cmd: z_scaled });
    };

    const handleStop = () => {
        telemetryService.sendTwistCommand(robotId, { linear_x_cmd: 0, angular_z_cmd: 0 });
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? 'none' : 'auto' }}>
            <h4 style={{ marginBottom: '2rem', color: '#333' }}>Manual Control (Twist)</h4>
            <div style={{ padding: '20px', background: '#f5f5f5', borderRadius: '50%', boxShadow: 'inset 0 2px 5px rgba(0,0,0,0.2)' }}>
                <Joystick size={150} sticky={false} baseColor="#e0e0e0" stickColor="#0056b3" move={handleMove} stop={handleStop} />
            </div>
            <p style={{ marginTop: '1rem', color: '#666', fontSize: '0.9rem' }}>Drag to drive</p>
        </div>
    );
};

export default TeleopPad;
