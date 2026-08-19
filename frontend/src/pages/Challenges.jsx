import React from 'react';
import { motion } from 'framer-motion';
import { Zap, BrainCircuit, ShieldAlert } from 'lucide-react';
import { useTranslation } from '../contexts/TranslationContext';

const challenges = [
    {
        icon: Zap,
        titleKey: 'realtimePerformanceTitle',
        descKey: 'realtimePerformanceDesc'
    },
    {
        icon: BrainCircuit,
        titleKey: 'contextualAccuracyTitle',
        descKey: 'contextualAccuracyDesc'
    },
    {
        icon: ShieldAlert,
        titleKey: 'dataSecurityTitle',
        descKey: 'dataSecurityDesc'
    }
];

const Challenges = () => {
    const { t } = useTranslation();

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="max-w-4xl mx-auto space-y-12">
            <h1 className="text-4xl font-bold text-center">{t('challengesTitle')}</h1>
            <p className="text-lg text-gray-400 text-center max-w-3xl mx-auto">{t('challengesDescription')}</p>
        <div className="space-y-8">
            {challenges.map((challenge, index) => (
                <motion.div 
                    key={challenge.titleKey}
                    className="flex items-start gap-6 p-6 rounded-lg bg-white/5 dark:bg-gray-900/50 border border-gray-800/50"
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.2 }}
                >
                    <challenge.icon className="w-12 h-12 text-purple-400 mt-1 flex-shrink-0" />
                    <div>
                        <h3 className="text-xl font-bold">{t(challenge.titleKey)}</h3>
                        <p className="text-gray-400 mt-2">{t(challenge.descKey)}</p>
                    </div>
                </motion.div>
            ))}
        </div>
    </motion.div>
    );
};

export default Challenges;
