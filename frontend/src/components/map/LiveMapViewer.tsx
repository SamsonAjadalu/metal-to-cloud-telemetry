import React, { useState, useRef, useEffect } from 'react';
import { telemetryService, type TelemetryData } from '../../services/websocket';
import yaml from 'js-yaml';

interface LiveMapViewerProps {
    robotId: string;
    telemetry: TelemetryData | null;
    goalEnabled?: boolean;
}

const LiveMapViewer: React.FC<LiveMapViewerProps> = ({ robotId, telemetry, goalEnabled = false }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [goalToast, setGoalToast] = useState<string | null>(null);

    // Map configuration (simulating static map from DevOps/S3)
    const [mapLoaded, setMapLoaded] = useState(false);
    const mapImageRef = useRef<HTMLImageElement | null>(null);

    // Map Metadata state from YAML
    const [mapMeta, setMapMeta] = useState<{ resolution: number; originX: number; originY: number } | null>(null);

    // Scale factors: these would typically come from a map.yaml metadata file
    // For now we assume a simple map scale: 1 pixel = 0.05 meters (resolution)
    // const _resolution = 0.05;
    // const _originX = -10.0; // map origin in meters
    // const _originY = -10.0;

    // Fetch map via Nginx reverse proxy (avoids CORS issues)
    // Nginx proxies /maps/* → DigitalOcean Spaces bucket
    const mapId = telemetry?.map_id || 'map_01';
    const mapUrlPng = `/maps/${mapId}/${mapId}.png`;
    const mapUrlYaml = `/maps/${mapId}/${mapId}.yaml`;

    useEffect(() => {
        // Fetch YAML metadata
        fetch(mapUrlYaml)
            .then(res => res.text())
            .then(text => {
                const parsed = yaml.load(text) as any;
                if (parsed && typeof parsed.resolution === 'number' && Array.isArray(parsed.origin)) {
                    setMapMeta({
                        resolution: parsed.resolution,
                        originX: parsed.origin[0],
                        originY: parsed.origin[1]
                    });
                }
            })
            .catch(err => console.warn(`[LiveMapViewer] Failed to load yaml from ${mapUrlYaml}`, err));

        // Load PNG image
        const img = new Image();
        img.src = mapUrlPng;
        img.onload = () => {
            mapImageRef.current = img;
            setMapLoaded(true);
        };
        img.onerror = () => {
            console.warn(`[LiveMapViewer] Failed to load map from ${mapUrlPng}.`);
        };
    }, [mapUrlPng, mapUrlYaml]);

    useEffect(() => {
        if (mapLoaded) {
            drawMap();
        }
    }, [telemetry, mapLoaded]);

    const drawMap = () => {
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!canvas || !ctx || !mapImageRef.current) return;

        // Clear and draw map background
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Ensure image stretches to canvas while maintaining aspect ratio or filling
        // We'll fill the canvas drawing area
        ctx.drawImage(mapImageRef.current, 0, 0, canvas.width, canvas.height);

        // Draw robot pose if available
        if (telemetry) {
            drawRobot(ctx, telemetry.x, telemetry.y, telemetry.yaw, canvas.width, canvas.height);
        }
    };

    // Conversion from world meters to canvas pixels
    const worldToPixel = (x_m: number, y_m: number, canvasW: number, canvasH: number) => {
        if (!mapMeta || !mapImageRef.current) return { px: 0, py: 0 };
        
        // Calculate the scale between the original PNG and the currently rendered canvas size
        const scaleX = canvasW / mapImageRef.current.width;
        const scaleY = canvasH / mapImageRef.current.height;

        // Formula: Pixel = (World - Origin) / Resolution
        const originalPx = (x_m - mapMeta.originX) / mapMeta.resolution;
        const originalPy = mapImageRef.current.height - ((y_m - mapMeta.originY) / mapMeta.resolution);

        return { 
            px: originalPx * scaleX, 
            py: originalPy * scaleY 
        };
    };

    const pixelToWorld = (px: number, py: number, canvasW: number, canvasH: number) => {
        if (!mapMeta || !mapImageRef.current) return { x_m: 0, y_m: 0 };

        const scaleX = canvasW / mapImageRef.current.width;
        const scaleY = canvasH / mapImageRef.current.height;

        const originalPx = px / scaleX;
        const originalPy = py / scaleY;

        // Formula: World = (Pixel * Resolution) + Origin
        const x_m = (originalPx * mapMeta.resolution) + mapMeta.originX;
        const y_m = ((mapImageRef.current.height - originalPy) * mapMeta.resolution) + mapMeta.originY;
        
        return { x_m, y_m };
    };

    const drawRobot = (ctx: CanvasRenderingContext2D, x: number, y: number, yaw: number, cw: number, ch: number) => {
        const { px, py } = worldToPixel(x, y, cw, ch);

        ctx.save();
        ctx.translate(px, py);
        ctx.rotate(-yaw); // canvas rotation is clockwise, robotics yaw is CCW

        // Draw an arrow for the robot
        ctx.fillStyle = '#ff3b30'; // Red marker
        ctx.beginPath();
        ctx.moveTo(10, 0); // Tip
        ctx.lineTo(-8, -6); // Bottom left
        ctx.lineTo(-4, 0);  // Inner
        ctx.lineTo(-8, 6);  // Bottom right
        ctx.closePath();
        ctx.fill();

        ctx.restore();
    };

    const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!goalEnabled) return; // Only allow goal clicks in Auto Mode

        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;

        const { x_m, y_m } = pixelToWorld(clickX, clickY, canvas.width, canvas.height);

        // Dispatch goal to websocket
        telemetryService.sendGoalCommand(robotId, {
            x: parseFloat(x_m.toFixed(2)),
            y: parseFloat(y_m.toFixed(2)),
            yaw: 0.0
        });

        // Non-blocking toast instead of alert()
        setGoalToast(`Goal sent → X: ${x_m.toFixed(2)}, Y: ${y_m.toFixed(2)}`);
        setTimeout(() => setGoalToast(null), 3000);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
            <div style={{ position: 'relative', border: '2px solid #ddd', borderRadius: '8px', overflow: 'hidden', cursor: goalEnabled ? 'crosshair' : 'default', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', width: '100%', maxWidth: '500px' }}>
                {!mapLoaded && <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 1 }}>Loading Map...</div>}
                <canvas
                    ref={canvasRef}
                    width={400}
                    height={400}
                    onClick={handleCanvasClick}
                    style={{ display: 'block', width: '100%', height: 'auto' }}
                />
                {/* Goal sent toast notification */}
                {goalToast && (
                    <div style={{
                        position: 'absolute', bottom: '10px', left: '50%', transform: 'translateX(-50%)',
                        background: 'rgba(25, 135, 84, 0.9)', color: 'white', padding: '8px 16px',
                        borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, whiteSpace: 'nowrap',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.2)', zIndex: 2
                    }}>
                        ✓ {goalToast}
                    </div>
                )}
            </div>
            {goalEnabled && <p style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.85rem' }}>Click on the map to set a Nav2 Goal.</p>}
        </div>
    );
};

export default LiveMapViewer;
