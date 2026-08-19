import React, { useEffect, useState } from 'react';

const CursorGlow = () => {
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

    useEffect(() => {
        const updateMousePosition = (e) => {
            setMousePosition({ x: e.clientX, y: e.clientY });
        };

        window.addEventListener('mousemove', updateMousePosition);

        return () => {
            window.removeEventListener('mousemove', updateMousePosition);
        };
    }, []);

    return (
        <div
            className="fixed pointer-events-none"
            style={{
                left: `${mousePosition.x}px`,
                top: `${mousePosition.y}px`,
                transform: 'translate(-50%, -50%)',
                zIndex: 1,
            }}
        >
            {/* Large outer glow */}
            <div
                className="w-32 h-32 rounded-full opacity-30"
                style={{
                    background: 'radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, rgba(168, 85, 247, 0.05) 40%, transparent 70%)',
                    filter: 'blur(20px)',
                }}
            />
            
            {/* Medium glow */}
            <div
                className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full opacity-40"
                style={{
                    background: 'radial-gradient(circle, rgba(168, 85, 247, 0.2) 0%, rgba(168, 85, 247, 0.1) 50%, transparent 70%)',
                    filter: 'blur(10px)',
                }}
            />
            
            {/* Small inner glow */}
            <div
                className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full opacity-50"
                style={{
                    background: 'radial-gradient(circle, rgba(168, 85, 247, 0.3) 0%, rgba(168, 85, 247, 0.15) 60%, transparent 80%)',
                    filter: 'blur(5px)',
                }}
            />
        </div>
    );
};

export default CursorGlow;
