import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Building, Pencil, Loader2, Check, X, ShieldCheck, HeartPulse, BriefcaseBusiness, Home, Landmark, Users, BadgeInfo } from 'lucide-react';
import Button from '../components/ui/Button';
import { useTranslation } from '../contexts/TranslationContext';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../services/api';

const genderOptions = ['Male', 'Female', 'Non-binary', 'Prefer not to say', 'Other'];
const maritalStatusOptions = ['Single', 'Married', 'Divorced', 'Widowed', 'Separated'];
const familyStatusOptions = ['Nuclear family', 'Joint family', 'Single parent family', 'Extended family', 'Other'];
const employmentStatusOptions = ['Employed', 'Self-employed', 'Freelancer', 'Student', 'Unemployed', 'Retired'];
const educationOptions = ['Primary', 'Secondary', 'Diploma', 'Graduate', 'Postgraduate', 'Doctorate', 'Other'];
const yesNoOptions = ['No', 'Yes'];
const smokerOptions = ['No', 'Yes', 'Occasionally'];
const alcoholOptions = ['No', 'Occasionally', 'Regularly'];

const profileSections = [
    {
        title: 'Personal details',
        icon: BadgeInfo,
        fields: [
            { key: 'name', label: 'Full name', icon: User, type: 'text', required: true },
            { key: 'email', label: 'Email address', icon: Mail, type: 'email', disabled: true },
            { key: 'phone', label: 'Phone number', icon: BadgeInfo, type: 'tel', required: true, pattern: '^\\d{7,15}$', helper: 'Digits only, 7 to 15 characters.' },
            { key: 'age', label: 'Age', icon: BadgeInfo, type: 'number', required: true, min: 0, max: 150 },
            { key: 'date_of_birth', label: 'Date of birth', icon: BadgeInfo, type: 'date' },
            { key: 'gender', label: 'Gender', icon: BadgeInfo, type: 'select', required: true, options: genderOptions },
            { key: 'citizenship', label: 'Citizenship', icon: Landmark, type: 'text', required: true },
            { key: 'address', label: 'Residential address', icon: Home, type: 'textarea', required: true },
            { key: 'country', label: 'Country', icon: Landmark, type: 'text', required: true },
            { key: 'state', label: 'State / Region', icon: Landmark, type: 'text', required: true },
            { key: 'city', label: 'City', icon: Home, type: 'text', required: true },
            { key: 'pin_code', label: 'PIN / ZIP code', icon: Home, type: 'text', required: true, pattern: '^\\d{4,10}$', helper: 'Digits only, 4 to 10 characters.' },
        ],
    },
    {
        title: 'Family and household',
        icon: Users,
        fields: [
            { key: 'marital_status', label: 'Marital status', icon: Users, type: 'select', required: true, options: maritalStatusOptions },
            { key: 'family_status', label: 'Family status', icon: Users, type: 'select', options: familyStatusOptions },
            { key: 'father_name', label: "Father's name", icon: Users, type: 'text' },
            { key: 'mother_name', label: "Mother's name", icon: Users, type: 'text' },
            { key: 'dependents_count', label: 'Number of dependents', icon: Users, type: 'number', min: 0, max: 50 },
            { key: 'nominee_name', label: 'Nominee name', icon: Users, type: 'text' },
            { key: 'nominee_relation', label: 'Nominee relationship', icon: Users, type: 'text' },
            { key: 'emergency_contact_name', label: 'Emergency contact name', icon: Users, type: 'text', required: true },
            { key: 'emergency_contact_phone', label: 'Emergency contact phone', icon: Users, type: 'tel', required: true, pattern: '^\\d{7,15}$', helper: 'Digits only, 7 to 15 characters.' },
        ],
    },
    {
        title: 'Employment and income',
        icon: BriefcaseBusiness,
        fields: [
            { key: 'occupation', label: 'Occupation / job title', icon: BriefcaseBusiness, type: 'text', required: true },
            { key: 'employer', label: 'Employer / business name', icon: BriefcaseBusiness, type: 'text' },
            { key: 'employment_status', label: 'Employment status', icon: BriefcaseBusiness, type: 'select', required: true, options: employmentStatusOptions },
            { key: 'annual_income', label: 'Annual income', icon: BriefcaseBusiness, type: 'text', required: true },
            { key: 'education_level', label: 'Education level', icon: BriefcaseBusiness, type: 'select', options: educationOptions },
        ],
    },
    {
        title: 'Health and risk factors',
        icon: HeartPulse,
        fields: [
            { key: 'disability_status', label: 'Disability status', icon: HeartPulse, type: 'select', options: yesNoOptions },
            { key: 'critical_illness', label: 'Critical illness history', icon: HeartPulse, type: 'select', options: yesNoOptions },
            { key: 'smoker_status', label: 'Smoking status', icon: HeartPulse, type: 'select', required: true, options: smokerOptions },
            { key: 'alcohol_use', label: 'Alcohol use', icon: HeartPulse, type: 'select', options: alcoholOptions },
            { key: 'existing_conditions', label: 'Existing medical conditions', icon: HeartPulse, type: 'textarea', required: true },
            { key: 'insurance_history', label: 'Previous insurance / claim history', icon: HeartPulse, type: 'textarea' },
        ],
    },
];

const emptyForm = {
    name: '',
    organization: '',
    phone: '',
    age: '',
    date_of_birth: '',
    gender: '',
    marital_status: '',
    family_status: '',
    father_name: '',
    mother_name: '',
    citizenship: '',
    disability_status: '',
    critical_illness: '',
    occupation: '',
    employer: '',
    annual_income: '',
    employment_status: '',
    education_level: '',
    address: '',
    country: '',
    state: '',
    city: '',
    pin_code: '',
    dependents_count: '',
    smoker_status: '',
    alcohol_use: '',
    existing_conditions: '',
    insurance_history: '',
    nominee_name: '',
    nominee_relation: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
};

const buildFormFromUser = (user) => ({
    ...emptyForm,
    name: user.name || '',
    organization: user.organization || '',
    phone: user.phone || '',
    age: user.age ?? '',
    date_of_birth: user.date_of_birth || '',
    gender: user.gender || '',
    marital_status: user.marital_status || '',
    family_status: user.family_status || '',
    father_name: user.father_name || '',
    mother_name: user.mother_name || '',
    citizenship: user.citizenship || '',
    disability_status: user.disability_status || '',
    critical_illness: user.critical_illness || '',
    occupation: user.occupation || '',
    employer: user.employer || '',
    annual_income: user.annual_income || '',
    employment_status: user.employment_status || '',
    education_level: user.education_level || '',
    address: user.address || '',
    country: user.country || '',
    state: user.state || '',
    city: user.city || '',
    pin_code: user.pin_code || '',
    dependents_count: user.dependents_count ?? '',
    smoker_status: user.smoker_status || '',
    alcohol_use: user.alcohol_use || '',
    existing_conditions: user.existing_conditions || '',
    insurance_history: user.insurance_history || '',
    nominee_name: user.nominee_name || '',
    nominee_relation: user.nominee_relation || '',
    emergency_contact_name: user.emergency_contact_name || '',
    emergency_contact_phone: user.emergency_contact_phone || '',
});

const formatValue = (value) => {
    if (value === null || value === undefined || value === '') return '—';
    return String(value);
};

// --- BACKEND INTEGRATION POINT (was: hard-coded dummy userData) ---
// Real profile data comes from AuthContext, which is populated from
// GET /api/auth/me. Editing goes through PATCH /api/users/me.

const Profile = () => {
    const { t } = useTranslation();
    const { user, isLoggedIn, isLoading, logout, refreshUser, openLoginModal } = useAuth();
    const [isEditing, setIsEditing] = useState(false);
    const [form, setForm] = useState(emptyForm);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState(null);
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    if (isLoading) {
        return <div className="flex-1 flex items-center justify-center py-16"><Loader2 className="w-8 h-8 animate-spin text-purple-400" /></div>;
    }

    if (!isLoggedIn) {
        return (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md mx-auto text-center py-16 space-y-4">
                <User className="w-10 h-10 text-purple-400 mx-auto" />
                <p className="text-gray-400">Sign in to view and manage your profile.</p>
                <Button onClick={openLoginModal}>{t('signIn')}</Button>
            </motion.div>
        );
    }

    const startEditing = () => {
        setForm(buildFormFromUser(user));
        setError(null);
        setIsEditing(true);
    };

    const handleSave = async (event) => {
        event?.preventDefault();
        setIsSaving(true);
        setError(null);
        try {
            await api.updateProfile({
                ...form,
                age: form.age === '' ? null : Number(form.age),
                dependents_count: form.dependents_count === '' ? null : Number(form.dependents_count),
            });
            await refreshUser();
            setIsEditing(false);
        } catch (err) {
            setError(err.message || 'Could not save changes.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleLogout = async () => {
        setIsLoggingOut(true);
        await logout();
        setIsLoggingOut(false);
    };

    const renderField = (field) => {
        const FieldIcon = field.icon;
        const value = form[field.key];

        return (
            <div key={field.key} className={`space-y-2 ${field.key === 'address' || field.key === 'existing_conditions' || field.key === 'insurance_history' ? 'sm:col-span-2' : ''}`}>
                <label className="flex items-center gap-2 text-sm text-gray-400">
                    <FieldIcon className="w-4 h-4 text-purple-400" />
                    <span>{field.label}</span>
                    {field.required && <span className="text-red-400">*</span>}
                </label>
                {field.type === 'select' ? (
                    <select
                        value={value}
                        required={field.required}
                        disabled={field.disabled}
                        onChange={(e) => setForm((prev) => ({ ...prev, [field.key]: e.target.value }))}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-60"
                    >
                        <option value="">Select {field.label.toLowerCase()}</option>
                        {field.options.map((option) => (
                            <option key={option} value={option}>{option}</option>
                        ))}
                    </select>
                ) : field.type === 'textarea' ? (
                    <textarea
                        value={value}
                        required={field.required}
                        rows={field.key === 'address' ? 3 : 4}
                        disabled={field.disabled}
                        onChange={(e) => setForm((prev) => ({ ...prev, [field.key]: e.target.value }))}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-60"
                    />
                ) : (
                    <input
                        type={field.type}
                        min={field.min}
                        max={field.max}
                        pattern={field.pattern}
                        inputMode={field.type === 'tel' || field.key === 'pin_code' || field.key === 'phone' ? 'numeric' : undefined}
                        value={value}
                        required={field.required}
                        disabled={field.disabled}
                        onChange={(e) => setForm((prev) => ({ ...prev, [field.key]: e.target.value }))}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-60"
                    />
                )}
                {field.helper && <p className="text-xs text-gray-500">{field.helper}</p>}
            </div>
        );
    };

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto">
            <h1 className="text-4xl font-bold text-center mb-3">{t('profileTitle')}</h1>
            <p className="text-center text-gray-400 mb-8 max-w-3xl mx-auto">
                Add the personal, family, employment, and health details needed to tailor insurance advice.
            </p>
            <div className="p-6 sm:p-8 rounded-lg bg-white/5 dark:bg-gray-900/50 border border-gray-800/50 space-y-6">
                {user.role === 'admin' && (
                    <div className="flex items-center gap-2 text-sm text-purple-300 bg-purple-500/10 border border-purple-500/30 rounded-lg px-3 py-2 w-fit">
                        <ShieldCheck className="w-4 h-4" /> Administrator
                    </div>
                )}

                {isEditing ? (
                    <form onSubmit={handleSave} className="space-y-8">
                        {profileSections.map((group) => (
                            <div key={group.title} className="space-y-4">
                                <div className="flex items-center gap-2 text-gray-200">
                                    <group.icon className="w-5 h-5 text-purple-400" />
                                    <h2 className="text-lg font-semibold">{group.title}</h2>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {group.fields.map(renderField)}
                                </div>
                            </div>
                        ))}

                        {error && <p className="text-sm text-red-400">{error}</p>}

                        <div className="flex gap-3 pt-2">
                            <Button type="submit" disabled={isSaving} className="flex items-center gap-2">
                                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                                Save
                            </Button>
                            <Button type="button" variant="secondary" onClick={() => setIsEditing(false)} className="flex items-center gap-2">
                                <X className="w-4 h-4" /> Cancel
                            </Button>
                        </div>
                    </form>
                ) : (
                    <div className="space-y-8">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="flex items-center gap-4">
                                <User className="w-6 h-6 text-purple-400" />
                                <div>
                                    <p className="text-sm text-gray-400">{t('nameLabel')}</p>
                                    <p className="font-semibold">{formatValue(user.name)}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <Mail className="w-6 h-6 text-purple-400" />
                                <div>
                                    <p className="text-sm text-gray-400">{t('emailLabel')}</p>
                                    <p className="font-semibold">{formatValue(user.email)}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <Building className="w-6 h-6 text-purple-400" />
                                <div>
                                    <p className="text-sm text-gray-400">{t('organizationLabel')}</p>
                                    <p className="font-semibold">{formatValue(user.organization)}</p>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {profileSections.flatMap((group) => group.fields).map((field) => (
                                <div key={field.key} className="rounded-lg border border-gray-800/60 bg-black/20 p-4">
                                    <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">{field.label}</p>
                                    <p className="font-semibold text-gray-100 break-words">{formatValue(user[field.key])}</p>
                                </div>
                            ))}
                        </div>

                        <div className="flex gap-3 pt-4">
                            <Button variant="secondary" onClick={startEditing} className="flex items-center gap-2">
                                <Pencil className="w-4 h-4" /> Edit
                            </Button>
                            <Button variant="danger" onClick={handleLogout} disabled={isLoggingOut} className="flex items-center gap-2">
                                {isLoggingOut && <Loader2 className="w-4 h-4 animate-spin" />}
                                {t('logoutButton')}
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default Profile;
