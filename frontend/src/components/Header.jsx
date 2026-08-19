import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, ShieldCheck, Menu, X, Languages, Home, Users, FileText, Target, User, Loader2 } from 'lucide-react';
import { useTranslation } from '../contexts/TranslationContext';
import { useAuth } from '../contexts/AuthContext';

const Header = ({ role, setPage, activePage, theme, toggleTheme }) => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const { t } = useTranslation();

    const navItems = [
        { id: 'home', label: t('home'), icon: Home },
        { id: 'problem', label: t('problem'), icon: FileText },
        { id: 'challenges', label: t('challenges'), icon: Target },
        { id: 'contact', label: t('contactUs'), icon: Users },
        { id: 'profile', label: t('profile'), icon: User },
    ];

    const NavLink = ({ id, label, icon: Icon }) => (
        <button
            onClick={() => { setPage(id); setIsMenuOpen(false); }}
            className={`px-2 py-2 lg:px-3 lg:py-2 rounded-md text-sm font-medium transition-colors duration-300 relative flex items-center gap-1 lg:gap-2 ${
                activePage === id
                    ? 'text-white'
                    : 'text-gray-400 hover:text-white'
            }`}
        >
            <Icon className="w-4 h-4" />
            <span className="hidden lg:block">{label}</span>
            {activePage === id && (
                <motion.div
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ 
                        duration: 0.05
                    }}
                />
            )}
        </button>
    );

    return (
        <header className="fixed top-0 left-0 right-0 z-50 border-b border-gray-800/50 bg-black/90 backdrop-blur-lg">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-14 sm:h-16 min-h-14 sm:min-h-16">
                    <div className="flex items-center">
                        <div className="flex-shrink-0 flex items-center gap-2 sm:gap-3 cursor-pointer" onClick={() => setPage('home')}>
                             <Bot className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-purple-400" />
                            <h1 className="text-base sm:text-lg lg:text-xl font-bold tracking-wider">
                                Team <span className="text-purple-400">CRuX</span>
                            </h1>
                        </div>
                        <div className="hidden md:block">
                            <div className="ml-4 lg:ml-10 flex items-baseline space-x-1 lg:space-x-4">
                                {navItems.map(item => <NavLink key={item.id} {...item} />)}
                            </div>
                        </div>
                    </div>
                    <div className="hidden md:flex items-center gap-3 lg:gap-4">
                        {role === 'admin' && (
                            <div className="flex items-center gap-2 px-2 py-1 lg:px-3 lg:py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30">
                                <ShieldCheck className="w-3 h-3 lg:w-4 lg:h-4 text-purple-400" />
                                <span className="text-xs font-medium text-purple-300 hidden lg:block">Admin</span>
                            </div>
                        )}
                        <LanguageSwitcher />
                        <AuthButton />
                    </div>
                    <div className="flex md:hidden items-center gap-2">
                        {/* Mobile Language Switcher */}
                        <LanguageSwitcher />
                        
                        {/* Mobile Auth Button */}
                        <AuthButton />
                        
                        {/* Mobile Menu Button */}
                        <button 
                            onClick={() => setIsMenuOpen(!isMenuOpen)} 
                            className="p-2 inline-flex items-center justify-center rounded-md text-gray-400 hover:text-white hover:bg-gray-800"
                        >
                            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                        </button>
                    </div>
                </div>
            </div>
            {isMenuOpen && (
                <div className="md:hidden">
                    <div className="px-2 pt-2 pb-3 space-y-1 bg-black/95 border-t border-gray-800/50">
                        {/* Admin Badge for Mobile */}
                        {role === 'admin' && (
                            <div className="flex items-center justify-center gap-2 px-3 py-2 mb-2 rounded-md bg-purple-500/10 border border-purple-500/30">
                                <ShieldCheck className="w-4 h-4 text-purple-400" />
                                <span className="text-sm font-medium text-purple-300">Admin Panel</span>
                            </div>
                        )}
                        
                        {/* Navigation Items */}
                        {navItems.map(item => (
                            <button
                                key={item.id}
                                onClick={() => { setPage(item.id); setIsMenuOpen(false); }}
                                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium flex items-center gap-3 ${
                                    activePage === item.id ? 'text-white bg-purple-600/20' : 'text-gray-400 hover:text-white hover:bg-gray-800'
                                }`}
                            >
                                <item.icon className="w-4 h-4" />
                                {item.label}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </header>
    );
};

const LanguageSwitcher = () => {
    const [isOpen, setIsOpen] = useState(false);
    const { currentLanguage, changeLanguage } = useTranslation();

    const languages = [
        { code: 'en', name: 'English', nativeName: 'English' },
        { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
        { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
        { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
        { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
        { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી' },
        { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
        { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
        { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം' },
        { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' }
    ];

    const handleLanguageSelect = (language) => {
        changeLanguage(language.code);
        setIsOpen(false);
    };

    const currentLang = languages.find(lang => lang.code === currentLanguage) || languages[0];

    return (
        <div className="relative">
            <button 
                className="p-1.5 lg:p-2 rounded-full hover:bg-gray-800 transition-colors" 
                title="Change Language"
                onClick={() => setIsOpen(!isOpen)}
            >
                <Languages className="w-4 h-4 lg:w-5 lg:h-5 text-gray-400" />
            </button>

            {/* Language Dropdown */}
            {isOpen && (
                <motion.div
                    className="absolute top-full right-0 mt-2 w-40 sm:w-48 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto"
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    transition={{ duration: 0.15 }}
                >
                    <div className="p-2">
                        <div className="text-xs text-gray-400 px-2 py-1 mb-1">Select Language</div>
                        {languages.map((language) => (
                            <button
                                key={language.code}
                                onClick={() => handleLanguageSelect(language)}
                                className={`w-full text-left px-2 sm:px-3 py-2 rounded-md text-xs sm:text-sm hover:bg-gray-800 transition-colors flex items-center justify-between ${
                                    currentLanguage === language.code ? 'bg-purple-600/20 text-purple-300' : 'text-gray-300'
                                }`}
                            >
                                <span>{language.name}</span>
                                <span className="text-xs text-gray-500 hidden sm:block">{language.nativeName}</span>
                            </button>
                        ))}
                    </div>
                </motion.div>
            )}

            {/* Backdrop to close dropdown */}
            {isOpen && (
                <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setIsOpen(false)}
                />
            )}
        </div>
    );
};

const AuthButton = () => {
    // --- BACKEND INTEGRATION POINT (was: local fake isLoggedIn toggle) ---
    const { isLoggedIn, isLoading, openLoginModal, logout } = useAuth();
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    const handleClick = async () => {
        if (isLoggedIn) {
            setIsLoggingOut(true);
            await logout();
            setIsLoggingOut(false);
        } else {
            openLoginModal();
        }
    };

    return (
        <button
            onClick={handleClick}
            disabled={isLoading || isLoggingOut}
            className="flex items-center gap-1 lg:gap-2 px-2 lg:px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-60 text-white rounded-lg text-sm font-medium transition-colors"
        >
            {isLoggingOut ? <Loader2 className="w-4 h-4 animate-spin" /> : <User className="w-4 h-4" />}
            <span className="hidden sm:block">{isLoggedIn ? 'Sign Out' : 'Sign In'}</span>
        </button>
    );
};

export default Header;
