// src/contexts/AuthContext.jsx
//
// Replaces App.jsx's fake checkUserRole() and Home.jsx's local isLoggedIn
// state with real authenticated session handling. The role shown in the UI
// always comes from the backend's verified /api/auth/me response - never
// from anything stored locally - per spec section 5's "frontend should not
// trust a locally stored role" requirement.
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import * as api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null); // { id, name, email, organization, role, created_at }
    const [isLoading, setIsLoading] = useState(true);
    const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
    const [authError, setAuthError] = useState(null);

    const loadCurrentUser = useCallback(async () => {
        if (!api.getAccessToken()) {
            setUser(null);
            setIsLoading(false);
            return;
        }
        try {
            const me = await api.getCurrentUser();
            setUser(me);
        } catch {
            api.clearTokens();
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadCurrentUser();
    }, [loadCurrentUser]);

    const login = useCallback(async (email, password) => {
        setAuthError(null);
        try {
            await api.login({ email, password });
            await loadCurrentUser();
            setIsLoginModalOpen(false);
            return true;
        } catch (err) {
            setAuthError(err.message || 'Login failed.');
            return false;
        }
    }, [loadCurrentUser]);

    const register = useCallback(async (payload) => {
        setAuthError(null);
        try {
            await api.register(payload);
            await loadCurrentUser();
            setIsLoginModalOpen(false);
            return true;
        } catch (err) {
            setAuthError(err.message || 'Registration failed.');
            return false;
        }
    }, [loadCurrentUser]);

    const logout = useCallback(async () => {
        await api.logout();
        setUser(null);
    }, []);

    const openLoginModal = useCallback(() => {
        setAuthError(null);
        setIsLoginModalOpen(true);
    }, []);

    const closeLoginModal = useCallback(() => {
        setIsLoginModalOpen(false);
        setAuthError(null);
    }, []);

    const value = {
        user,
        isLoggedIn: !!user,
        role: user?.role || 'user',
        isLoading,
        login,
        register,
        logout,
        refreshUser: loadCurrentUser,
        isLoginModalOpen,
        openLoginModal,
        closeLoginModal,
        authError,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
    return ctx;
};
