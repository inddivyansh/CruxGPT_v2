import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import Input from '../components/ui/Input';
import Textarea from '../components/ui/Textarea';
import Button from '../components/ui/Button';
import { useTranslation } from '../contexts/TranslationContext';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../services/api';

const Suggestions = () => {
    const [submitted, setSubmitted] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const { t } = useTranslation();
    const { isLoggedIn, user } = useAuth();

    // --- BACKEND INTEGRATION POINT (was: commented-out fetch placeholder) ---
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        const formData = new FormData(e.target);
        const payload = {
            email: isLoggedIn ? user.email : formData.get('email'),
            organization: isLoggedIn ? user.organization : formData.get('organization'),
            contact: formData.get('contact'),
            suggestion: formData.get('suggestion'),
        };

        try {
            await api.submitSuggestion(payload);
            setSubmitted(true);
        } catch (err) {
            setError(err.message || 'Could not submit your suggestion. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (submitted) {
        return (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
                <h2 className="text-2xl font-bold text-green-400">{t('suggestionsSubmitted')}</h2>
                <p className="text-gray-400 mt-2">{t('suggestionsSubmittedDesc')}</p>
            </motion.div>
        );
    }

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-2xl mx-auto">
            <h1 className="text-3xl sm:text-4xl font-bold text-center mb-8 text-gray-100">{t('suggestionsTitle')}</h1>
            <p className="text-lg text-gray-400 text-center mb-8">{t('suggestionsDescription')}</p>
            <form onSubmit={handleSubmit} className="space-y-6 p-6 sm:p-8 rounded-lg bg-gray-800/50 border border-gray-700/50">
                {!isLoggedIn && (
                    <>
                        <Input name="email" type="email" placeholder={t('emailPlaceholder')} required />
                        <Input name="organization" type="text" placeholder={t('organizationPlaceholder')} />
                    </>
                )}
                {isLoggedIn && (
                    <p className="text-sm text-gray-400">
                        Submitting as <span className="text-gray-200">{user.email}</span>
                        {user.organization ? ` (${user.organization})` : ''}
                    </p>
                )}
                <Input name="contact" type="text" placeholder={t('contactPlaceholder')} />
                <Textarea name="suggestion" placeholder={t('suggestionPlaceholder')} rows="5" required />

                {error && <p className="text-sm text-red-400">{error}</p>}

                <Button type="submit" disabled={isSubmitting} className="w-full flex items-center justify-center gap-2">
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    {t('submitButton')}
                </Button>
            </form>
        </motion.div>
    );
};

export default Suggestions;
