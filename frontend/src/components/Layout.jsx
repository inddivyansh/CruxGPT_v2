import React from 'react';
import Header from './Header';
import Footer from './Footer';
import CursorGlow from './CursorGlow';
import FloatingChatButton from './FloatingChatButton';
import { useTheme } from '../hooks/useTheme';

const Layout = ({ children, role, setPage, activePage }) => {
    const [theme, toggleTheme] = useTheme();
    
    // Don't show floating chat button on home and profile pages
    const showFloatingChat = activePage !== 'home' && activePage !== 'profile';

    return (
        <div className="min-h-screen w-full overflow-x-hidden flex flex-col font-jetbrains-mono bg-black text-gray-200 relative">
            <CursorGlow />
            <Header role={role} setPage={setPage} activePage={activePage} theme={theme} toggleTheme={toggleTheme} />
            <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8 lg:py-12 pt-20 sm:pt-24 md:pt-28 lg:pt-32 xl:pt-36 relative z-10">
                {children}
            </main>
            <Footer />
            {showFloatingChat && <FloatingChatButton setPage={setPage} />}
        </div>
    );
};

export default Layout;
