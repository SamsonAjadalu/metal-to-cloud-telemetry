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
            telemetryService.sendTwistCommand(robotId, { linear_x: 0, angular_z: 0 });
            return;
        }

        const max_velocity = 0.5; // m/s
        const max_angular = 1.0; // rad/s

        // react-joystick-component gives x and y in cartesian plane based on joystick distance
        // event.x and event.y are normalized between -1 to 1 based on the size/distance of stick
        const x_scaled = event.y !== null ? (event.y / 50) * max_velocity : 0; // forward/backward
        const z_scaled = event.x !== null ? -(event.x / 50) * max_angular : 0; // Negative X is left rotation (positive angular) in robotics

        telemetryService.sendTwistCommand(robotId, { linear_x: x_scaled, angular_z: z_scaled });
    };

    const handleStop = () => {
        telemetryService.sendTwistCommand(robotId, { linear_x: 0, angular_z: 0 });
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
