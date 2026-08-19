import React, { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { TranslationProvider } from './contexts/TranslationContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import AuthModal from './components/AuthModal';
import Home from './pages/Home';
import ProblemStatement from './pages/ProblemStatement';
import Challenges from './pages/Challenges';
import ContactUs from './pages/ContactUs';
import Profile from './pages/Profile';
import AdminView from './components/AdminView';

// --- BACKEND INTEGRATION POINT (was: fake checkUserRole()) ---
// Role now comes from AuthContext, which resolves it from the backend's
// verified GET /api/auth/me response - never from anything stored locally.

const AppShell = () => {
    const [page, setPage] = useState('home');
    const { role, isLoading } = useAuth();

    const renderPage = () => {
        if (isLoading) {
            return <div className="flex-1 flex items-center justify-center text-gray-400">Loading...</div>;
        }
        if (role === 'admin') {
            return <AdminView />;
        }
        switch (page) {
            case 'home': return <Home />;
            case 'problem': return <ProblemStatement />;
            case 'challenges': return <Challenges />;
            case 'contact': return <ContactUs />;
            case 'profile': return <Profile />;
            default: return <Home />;
        }
    };

    return (
        <Layout role={role} setPage={setPage} activePage={page}>
            <AnimatePresence mode="wait">
                {renderPage()}
            </AnimatePresence>
            <AnimatePresence>
                <AuthModal />
            </AnimatePresence>
        </Layout>
    );
};

const App = () => {
    return (
        <TranslationProvider>
            <AuthProvider>
                <AppShell />
            </AuthProvider>
        </TranslationProvider>
    );
};

export default App;
