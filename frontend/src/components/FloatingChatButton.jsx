import React from 'react';
import { motion } from 'framer-motion';
import { MessageCircle } from 'lucide-react';

const FloatingChatButton = ({ setPage }) => {
    const handleChatClick = () => {
        // Set flag to open enhanced chat and navigate to home
        localStorage.setItem('openChat', 'true');
        setPage('home');
    };

    return (
        <motion.button
            className="fixed bottom-6 right-6 w-14 h-14 bg-purple-600 hover:bg-purple-700 text-white rounded-full shadow-lg flex items-center justify-center z-40"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={handleChatClick}
        >
            <MessageCircle className="w-6 h-6" />
        </motion.button>
    );
};

export default FloatingChatButton;
