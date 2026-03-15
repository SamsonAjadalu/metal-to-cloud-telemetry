import React, { useRef, useEffect, useState } from 'react';

export interface TrajectoryFrame {
    timestamp: string | number;
    x: number;
    y: number;
    yaw: number;
}

interface TrajectoryViewerProps {
    data: TrajectoryFrame[];
}

const TrajectoryViewer: React.FC<TrajectoryViewerProps> = ({ data }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [playbackSpeed, setPlaybackSpeed] = useState(1);
    const requestRef = useRef<number>(0);
    const lastUpdateRef = useRef<number>(0);

    // Constants for drawing
    const canvasWidth = 800;
    const canvasHeight = 400;
    // Scaler to fit the path on canvas - to be computed dynamically based on data bounds
    const [bounds, setBounds] = useState({ minX: -10, maxX: 10, minY: -10, maxY: 10, scale: 20, offsetX: 400, offsetY: 200 });

    useEffect(() => {
        if (data.length > 0) {
            // Calculate bounding box of the trajectory to compute scale and offset
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            data.forEach(p => {
                if (p.x < minX) minX = p.x;
                if (p.x > maxX) maxX = p.x;
                if (p.y < minY) minY = p.y;
                if (p.y > maxY) maxY = p.y;
            });

            // Add padding
            minX -= 2; maxX += 2; minY -= 2; maxY += 2;

            const width = maxX - minX;
            const height = maxY - minY;

            const scaleX = canvasWidth / (width || 1);
            const scaleY = canvasHeight / (height || 1);
            const scale = Math.min(scaleX, scaleY); // Keep aspect ratio

            // Center offsets
            const offsetX = (canvasWidth - (width * scale)) / 2 - (minX * scale);
            const offsetY = (canvasHeight - (height * scale)) / 2 - (minY * scale);

            setBounds({ minX, maxX, minY, maxY, scale, offsetX, offsetY });
            // Reset playback when new data loads
            setCurrentIndex(0);
            setIsPlaying(false);
        }
    }, [data]);

    const worldToPixel = (x: number, y: number) => {
        const px = (x * bounds.scale) + bounds.offsetX;
        const py = canvasHeight - ((y * bounds.scale) + bounds.offsetY); // Invert Y
        return { px, py };
    };

    const drawFrame = () => {
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!canvas || !ctx || data.length === 0) return;

        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw Grid (Optional, but helps with viz)
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;

        const step = Math.max(1, Math.floor(100 / bounds.scale)); // Grid lines roughly every 100px
        const gridStartX = Math.floor(bounds.minX / step) * step;
        const gridEndX = Math.ceil(bounds.maxX / step) * step;
        const gridStartY = Math.floor(bounds.minY / step) * step;
        const gridEndY = Math.ceil(bounds.maxY / step) * step;

        for (let x = gridStartX; x <= gridEndX; x += step) {
            const { px } = worldToPixel(x, 0);
            ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, canvasHeight); ctx.stroke();
        }
        for (let y = gridStartY; y <= gridEndY; y += step) {
            const { py } = worldToPixel(0, y);
            ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(canvasWidth, py); ctx.stroke();
        }

        // Draw Full Path (Gray)
        ctx.beginPath();
        ctx.strokeStyle = '#cccccc';
        ctx.lineWidth = 4;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';

        data.forEach((p, i) => {
            const { px, py } = worldToPixel(p.x, p.y);
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        });
        ctx.stroke();

        // Draw Played Segment (Blue)
        if (currentIndex > 0) {
            ctx.beginPath();
            ctx.strokeStyle = '#0d6efd';
            ctx.lineWidth = 4;
            for (let i = 0; i <= currentIndex; i++) {
                const { px, py } = worldToPixel(data[i].x, data[i].y);
                if (i === 0) ctx.moveTo(px, py);
                else ctx.lineTo(px, py);
            }
            ctx.stroke();
        }

        // Draw Robot Head (Arrow) at current index
        const currentPose = data[currentIndex];
        const { px, py } = worldToPixel(currentPose.x, currentPose.y);

        ctx.save();
        ctx.translate(px, py);
        ctx.rotate(-currentPose.yaw); // CCW rotation

        ctx.fillStyle = '#ff3b30'; // Red marker
        ctx.beginPath();
        // Scale arrow size based on zoom, but clamp between 10 and 30 px
        const arrowSize = Math.max(10, Math.min(30, bounds.scale / 2));

        ctx.moveTo(arrowSize, 0);
        ctx.lineTo(-arrowSize * 0.8, -arrowSize * 0.6);
        ctx.lineTo(-arrowSize * 0.4, 0);
        ctx.lineTo(-arrowSize * 0.8, arrowSize * 0.6);
        ctx.closePath();
        ctx.fill();

        ctx.restore();
    };

    // Render loop for playback and drawing
    useEffect(() => {
        drawFrame(); // Initial draw 
    }, [currentIndex, bounds]);

    // Playback logic
    const animate = (time: number) => {
        if (!lastUpdateRef.current) lastUpdateRef.current = time;

        // Calculate delta time
        const deltaTime = time - lastUpdateRef.current;

        // Target update rate is ~1 frame per simulated second.
        // E.g. 1000ms / playbackSpeed amount of real time before advancing index
        const interval = 1000 / playbackSpeed;

        if (deltaTime >= interval) {
            setCurrentIndex(prev => {
                if (prev < data.length - 1) {
                    return prev + 1;
                } else {
                    setIsPlaying(false); // Stop when hitting the end
                    return prev;
                }
            });
            lastUpdateRef.current = time;
        }

        if (isPlayingRef.current) { // Use ref to prevent closure capture issues
            requestRef.current = requestAnimationFrame(animate);
        }
    };

    // Hacky way to read ref inside animate callback instead of dependency binding 
    const isPlayingRef = useRef(isPlaying);
    useEffect(() => {
        isPlayingRef.current = isPlaying;
        if (isPlaying) {
            lastUpdateRef.current = performance.now();
            requestRef.current = requestAnimationFrame(animate);
        } else {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        }
        return () => {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [isPlaying, playbackSpeed]);

    const togglePlay = () => {
        if (currentIndex >= data.length - 1) {
            setCurrentIndex(0); // Reset if at end
        }
        setIsPlaying(!isPlaying);
    };

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const idx = parseInt(e.target.value, 10);
        setCurrentIndex(idx);
        setIsPlaying(false); // Pause when scrubbing
    };

    if (data.length === 0) {
        return <div>No trajectory data to display. Please verify selection.</div>;
    }

    const currentFrame = data[currentIndex];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', maxWidth: '850px', margin: '0 auto' }}>

            <div style={{
                position: 'relative',
                border: '2px solid #ddd',
                borderRadius: '8px',
                overflow: 'hidden',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                background: '#f9f9f9',
                marginBottom: '1rem'
            }}>
                <canvas
                    ref={canvasRef}
                    width={canvasWidth}
                    height={canvasHeight}
                    style={{ display: 'block' }}
                />
            </div>

            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '1rem', background: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <button
                        onClick={togglePlay}
                        style={{
                            background: isPlaying ? '#dc3545' : '#198754',
                            color: 'white',
                            padding: '0.5rem 1.5rem',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontSize: '1rem',
                            minWidth: '100px'
                        }}
                    >
                        {isPlaying ? 'Pause' : 'Play'}
                    </button>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <label style={{ fontWeight: '500' }}>Speed:</label>
                        <select
                            value={playbackSpeed}
                            onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
                            style={{ padding: '0.3rem', borderRadius: '4px' }}
                        >
                            <option value={0.5}>0.5x</option>
                            <option value={1}>1.0x</option>
                            <option value={2}>2.0x</option>
                            <option value={5}>5.0x</option>
                        </select>
                    </div>

                    <div style={{ fontFamily: 'monospace', fontSize: '1.2rem', fontWeight: 'bold' }}>
                        {String(currentFrame.timestamp)}
                    </div>
                </div>

                <input
                    type="range"
                    min={0}
                    max={data.length - 1}
                    value={currentIndex}
                    onChange={handleSliderChange}
                    style={{ width: '100%', cursor: 'pointer' }}
                />

                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.9rem' }}>
                    <span>Start</span>
                    <span>End</span>
                </div>
            </div>
        </div>
    );
};

export default TrajectoryViewer;
