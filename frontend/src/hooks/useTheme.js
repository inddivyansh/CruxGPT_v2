import { useState, useEffect } from 'react';

export const useTheme = () => {
    // Always use dark theme
    const [theme, setTheme] = useState('dark');

    const toggleTheme = () => {
        // Disabled - always dark theme
        return;
    };

    useEffect(() => {
        // Always set dark theme
        document.documentElement.classList.add('dark');
    }, []);

    return [theme, toggleTheme];
};
