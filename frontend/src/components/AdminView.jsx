import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart2, CheckCircle, Clock, AlertTriangle, Database, SlidersHorizontal, ToggleLeft, ToggleRight, Loader2, Users, FileText, MessageSquare, ThumbsUp, ThumbsDown } from 'lucide-react';
import * as api from '../services/api';

// --- BACKEND INTEGRATION POINT (was: fake fetchAdminData with hard-coded 94.7% etc.) ---
// Real stats from GET /api/admin/stats. If there isn't enough feedback data
// yet, the backend honestly reports that instead of a fabricated accuracy
// number (spec section 60).

const AdminView = () => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        api
            .getAdminStats()
            .then((stats) => { if (!cancelled) setData(stats); })
            .catch((err) => { if (!cancelled) setError(err.message || 'Could not load admin statistics.'); });
        return () => { cancelled = true; };
    }, []);

    if (error) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center py-16">
                <AlertTriangle className="w-8 h-8 text-red-400" />
                <p className="text-gray-300">{error}</p>
            </div>
        );
    }

    if (!data) return <div className="flex-1 flex items-center justify-center py-16"><Loader2 className="w-8 h-8 animate-spin text-purple-400" /></div>;

    const isOperational = data.system_status === 'operational';
    const isRagActive = data.rag_pipeline === 'active';

    const stats = [
        { title: 'Overall Accuracy', value: typeof data.overall_accuracy === 'number' ? `${data.overall_accuracy}%` : data.overall_accuracy, icon: CheckCircle, color: 'text-green-400' },
        { title: 'Avg. Response Time', value: `${data.average_response_time}s`, icon: Clock, color: 'text-blue-400' },
        { title: 'Queries Today', value: data.queries_today, icon: BarChart2, color: 'text-yellow-400' },
        { title: 'System Status', value: isOperational ? 'Operational' : data.system_status, icon: isOperational ? CheckCircle : AlertTriangle, color: isOperational ? 'text-green-400' : 'text-red-400' },
    ];

    const secondaryStats = [
        { title: 'Total Users', value: data.total_users, icon: Users, color: 'text-purple-400' },
        { title: 'Total Documents', value: data.total_documents, icon: FileText, color: 'text-purple-400' },
        { title: 'Total Conversations', value: data.total_conversations, icon: MessageSquare, color: 'text-purple-400' },
        { title: 'Positive Feedback', value: data.positive_feedback, icon: ThumbsUp, color: 'text-green-400' },
        { title: 'Negative Feedback', value: data.negative_feedback, icon: ThumbsDown, color: 'text-red-400' },
    ];

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, index) => (
                    <motion.div key={stat.title} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: index * 0.1 }}>
                        <StatCard {...stat} />
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                {secondaryStats.map((stat, index) => (
                    <motion.div key={stat.title} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.4 + index * 0.05 }}>
                        <StatCard {...stat} small />
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ConfigCard title="API Configuration" icon={SlidersHorizontal}>
                    <p className="text-sm text-gray-400">
                        LLM and embedding providers are configured server-side via environment variables
                        (GEMINI_API_KEY, GEMINI_LLM_MODEL, GEMINI_EMBEDDING_MODEL) and are never exposed to
                        the frontend.
                    </p>
                </ConfigCard>
                <ConfigCard title="System Status" icon={Database}>
                     <FeatureToggle label="Maintenance Mode" enabled={data.maintenance_mode} />
                     <FeatureToggle label="RAG Pipeline" enabled={isRagActive} />
                </ConfigCard>
            </div>
        </motion.div>
    );
};

const StatCard = ({ title, value, icon: Icon, color, small }) => (
    <div className={`bg-gray-900/50 border border-gray-800/50 rounded-lg ${small ? 'p-4' : 'p-6'}`}>
        <div className="flex items-center justify-between"><p className={`font-medium text-gray-400 ${small ? 'text-xs' : 'text-sm'}`}>{title}</p><Icon className={`${small ? 'w-4 h-4' : 'w-6 h-6'} ${color}`} /></div>
        <p className={`mt-2 font-semibold ${color} ${small ? 'text-xl' : 'text-3xl'}`}>{value}</p>
    </div>
);

const ConfigCard = ({ title, icon: Icon, children }) => (
    <div className="bg-gray-900/50 border border-gray-800/50 p-6 rounded-lg">
        <div className="flex items-center gap-3 mb-4"><Icon className="w-6 h-6 text-purple-400" /><h3 className="text-xl font-bold">{title}</h3></div>
        <div className="space-y-4">{children}</div>
    </div>
);

// Read-only display - toggling these requires a real settings endpoint,
// which isn't part of the MVP (spec section 62), so the control is
// intentionally non-interactive rather than pretending to work.
const FeatureToggle = ({ label, enabled }) => (
    <div className="flex items-center justify-between text-sm">
        <span className="text-gray-300">{label}</span>
        <span className="flex items-center gap-2" title="Read-only - configured via backend environment variables">
            {enabled ? <ToggleRight className="w-10 h-10 text-green-400" /> : <ToggleLeft className="w-10 h-10 text-gray-500" />}
        </span>
    </div>
);

export default AdminView;
