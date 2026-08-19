import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Linkedin, Github, FileText, Loader2, Mail, MessageSquare, Users } from 'lucide-react';
import Input from '../components/ui/Input';
import Textarea from '../components/ui/Textarea';
import Button from '../components/ui/Button';
import { useTranslation } from '../contexts/TranslationContext';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../services/api';

const teamMembers = [
    {
        name: 'Divyansh Nagar',
        roleKey: 'teamLeadRole',
        avatar: 'https://placehold.co/128x128/1a1a1a/ffffff?text=DN',
        linkedin: 'https://www.linkedin.com/in/diivyaix/',
        github: 'https://github.com/inddivyansh',
        resume: 'https://drive.google.com/file/d/1NAz2yUwEnHH_Xun89C6N8MO8YoYKJtWM/view?usp=sharing',
    },
    
];

const ContactUs = () => {
    const [submitted, setSubmitted] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const { t } = useTranslation();
    const { isLoggedIn, user } = useAuth();

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
            setError(err.message || 'Could not submit your message. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-8 sm:space-y-12">
            <div className="text-center space-y-4 max-w-4xl mx-auto">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm mx-auto">
                    <Mail className="w-4 h-4" />
                    <span>{t('contactUs')}</span>
                </div>
                <h1 className="text-3xl sm:text-4xl font-bold text-center text-gray-100">{t('contactTitle')}</h1>
                <p className="text-lg text-gray-400 text-center max-w-3xl mx-auto">{t('contactDescription')}</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 items-start">
                <motion.div
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.45 }}
                    className="rounded-2xl bg-gray-800/50 border border-gray-700/50 p-6 sm:p-8"
                >
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 rounded-lg bg-purple-500/10 text-purple-300">
                            <MessageSquare className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-gray-100">{t('contactFormTitle')}</h2>
                            <p className="text-sm text-gray-400">{t('suggestionsDescription')}</p>
                        </div>
                    </div>

                    {submitted ? (
                        <div className="text-center py-10">
                            <h2 className="text-2xl font-bold text-green-400">{t('contactSubmitted')}</h2>
                            <p className="text-gray-400 mt-2">{t('contactSubmittedDesc')}</p>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-5">
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
                            <Textarea name="suggestion" placeholder={t('messagePlaceholder')} rows="6" required />

                            {error && <p className="text-sm text-red-400">{error}</p>}

                            <Button type="submit" disabled={isSubmitting} className="w-full flex items-center justify-center gap-2">
                                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                                {t('contactButton')}
                            </Button>
                        </form>
                    )}
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.55, delay: 0.1 }}
                    className="rounded-2xl bg-gray-800/30 border border-gray-700/40 p-6 sm:p-8"
                >
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-300">
                            <Users className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-gray-100">{t('teamTitle')}</h2>
                            <p className="text-sm text-gray-400">{t('aboutDescription')}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {teamMembers.map((member, index) => (
                            <motion.div
                                key={member.name}
                                className="p-4 rounded-xl bg-gray-900/40 border border-gray-700/40 text-center hover:bg-gray-800/60 transition-all duration-300"
                                initial={{ opacity: 0, y: 18 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.35, delay: index * 0.05 }}
                            >
                                <img
                                    src={member.avatar}
                                    alt={member.name}
                                    className="w-20 h-20 rounded-full mx-auto mb-3 border-2 border-purple-400"
                                />
                                <h3 className="text-base sm:text-lg font-bold text-gray-100">{member.name}</h3>
                                <p className="text-sm text-purple-400 mb-3">{t(member.roleKey)}</p>
                                <div className="flex justify-center gap-2">
                                    <a
                                        href={member.linkedin}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="p-2 rounded-full bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 hover:text-blue-300 transition-all duration-300"
                                        title="LinkedIn Profile"
                                    >
                                        <Linkedin size={16} />
                                    </a>
                                    <a
                                        href={member.github}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="p-2 rounded-full bg-gray-600/20 text-gray-400 hover:bg-gray-600/30 hover:text-gray-300 transition-all duration-300"
                                        title="GitHub Profile"
                                    >
                                        <Github size={16} />
                                    </a>
                                    <a
                                        href={member.resume}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="p-2 rounded-full bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 hover:text-purple-300 transition-all duration-300"
                                        title="Resume"
                                    >
                                        <FileText size={16} />
                                    </a>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </motion.div>
    );
};

export default ContactUs;
