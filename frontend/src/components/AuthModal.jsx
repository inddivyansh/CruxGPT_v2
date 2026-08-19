// src/components/AuthModal.jsx
//
// Real login/register modal backed by AuthContext. Rendered once at the App
// level and controlled via context state, so both the Header's "Sign In"
// button and Home's first-visit prompt open the same modal.
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from '../contexts/TranslationContext';

const genderOptions = ['Male', 'Female', 'Non-binary', 'Prefer not to say', 'Other'];
const maritalStatusOptions = ['Single', 'Married', 'Divorced', 'Widowed', 'Separated'];
const employmentStatusOptions = ['Employed', 'Self-employed', 'Freelancer', 'Student', 'Unemployed', 'Retired'];
const smokerStatusOptions = ['No', 'Yes', 'Occasionally'];
const yesNoOptions = ['No', 'Yes'];
const educationOptions = ['Primary', 'Secondary', 'Diploma', 'Graduate', 'Postgraduate', 'Doctorate', 'Other'];

const fieldLayoutClasses = {
    address: 'sm:col-span-2 xl:col-span-3',
    annual_income: 'sm:col-span-2',
    employer: 'sm:col-span-2',
    critical_illness: 'sm:col-span-2 xl:col-span-3',
    insurance_history: 'sm:col-span-2 xl:col-span-3',
    nominee_name: 'sm:col-span-2',
    nominee_relation: 'sm:col-span-2',
    family_status: 'sm:col-span-2',
};

const onboardingFields = [
    { name: 'phone', label: 'Phone number', type: 'tel', required: false, pattern: '^\\d{7,15}$', helper: 'Digits only, 7 to 15 characters.' },
    { name: 'age', label: 'Age', type: 'number', required: false, min: 0, max: 150 },
    { name: 'gender', label: 'Gender', type: 'select', required: false, options: genderOptions },
    { name: 'marital_status', label: 'Marital status', type: 'select', required: false, options: maritalStatusOptions },
    { name: 'citizenship', label: 'Citizenship', type: 'text', required: false },
    { name: 'occupation', label: 'Occupation / job title', type: 'text', required: false },
    { name: 'employment_status', label: 'Employment status', type: 'select', required: false, options: employmentStatusOptions },
    { name: 'annual_income', label: 'Annual income', type: 'text', required: false },
    { name: 'address', label: 'Residential address', type: 'text', required: false },
    { name: 'country', label: 'Country', type: 'text', required: false },
    { name: 'state', label: 'State / Region', type: 'text', required: false },
    { name: 'city', label: 'City', type: 'text', required: false },
    { name: 'pin_code', label: 'PIN / ZIP code', type: 'tel', required: false, pattern: '^\\d{4,10}$', helper: 'Digits only, 4 to 10 characters.' },
    { name: 'smoker_status', label: 'Smoking status', type: 'select', required: false, options: smokerStatusOptions },
    { name: 'existing_conditions', label: 'Existing medical conditions', type: 'select', required: false, options: yesNoOptions },
    { name: 'emergency_contact_name', label: 'Emergency contact name', type: 'text', required: false },
    { name: 'emergency_contact_phone', label: 'Emergency contact phone', type: 'tel', required: false, pattern: '^\\d{7,15}$', helper: 'Digits only, 7 to 15 characters.' },
    { name: 'education_level', label: 'Education level', type: 'select', required: false, options: educationOptions },
    { name: 'family_status', label: 'Family status', type: 'text', required: false },
    { name: 'father_name', label: "Father's name", type: 'text', required: false },
    { name: 'mother_name', label: "Mother's name", type: 'text', required: false },
    { name: 'disability_status', label: 'Disability status', type: 'select', required: false, options: yesNoOptions },
    { name: 'critical_illness', label: 'Critical illness history', type: 'text', required: false },
    { name: 'employer', label: 'Employer / business name', type: 'text', required: false },
    { name: 'date_of_birth', label: 'Date of birth', type: 'date', required: false },
    { name: 'dependents_count', label: 'Number of dependents', type: 'number', required: false, min: 0, max: 50 },
    { name: 'alcohol_use', label: 'Alcohol use', type: 'select', required: false, options: ['No', 'Occasionally', 'Regularly'] },
    { name: 'insurance_history', label: 'Previous insurance / claim history', type: 'text', required: false },
    { name: 'nominee_name', label: 'Nominee name', type: 'text', required: false },
    { name: 'nominee_relation', label: 'Nominee relationship', type: 'text', required: false },
];

const AuthModal = () => {
    const { isLoginModalOpen, closeLoginModal, login, register, authError } = useAuth();
    const { t } = useTranslation();
    const [isLogin, setIsLogin] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showOptionalProfile, setShowOptionalProfile] = useState(false);
    const [form, setForm] = useState({
        name: '',
        email: '',
        password: '',
        organization: '',
        phone: '',
        age: '',
        gender: '',
        marital_status: '',
        citizenship: '',
        occupation: '',
        employment_status: '',
        annual_income: '',
        address: '',
        country: '',
        state: '',
        city: '',
        pin_code: '',
        smoker_status: '',
        existing_conditions: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        education_level: '',
        family_status: '',
        father_name: '',
        mother_name: '',
        disability_status: '',
        critical_illness: '',
        employer: '',
        date_of_birth: '',
        dependents_count: '',
        alcohol_use: '',
        insurance_history: '',
        nominee_name: '',
        nominee_relation: '',
    });

    if (!isLoginModalOpen) return null;

    const renderField = (field) => {
        const fieldId = `signup-${field.name}`;
        const wrapperClassName = fieldLayoutClasses[field.name] || '';

        return (
            <div key={field.name} className={wrapperClassName}>
                <label htmlFor={fieldId} className="mb-1.5 flex items-center gap-2 text-sm font-medium text-gray-200">
                    <span>{field.label}</span>
                    <span className="text-xs font-normal text-gray-500">optional</span>
                </label>

                {field.type === 'select' ? (
                    <select
                        id={fieldId}
                        name={field.name}
                        value={form[field.name]}
                        onChange={handleChange}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-100"
                    >
                        <option value="">Select {field.label}</option>
                        {field.options.map((option) => (
                            <option key={option} value={option}>{option}</option>
                        ))}
                    </select>
                ) : (
                    <input
                        id={fieldId}
                        name={field.name}
                        type={field.type}
                        min={field.min}
                        max={field.max}
                        pattern={field.pattern}
                        placeholder={field.label}
                        value={form[field.name]}
                        onChange={handleChange}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                )}

                {field.helper && <p className="mt-1 text-xs text-gray-500">{field.helper}</p>}
            </div>
        );
    };

    const handleChange = (e) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        let ok = false;
        if (isLogin) {
            ok = await login(form.email, form.password);
        } else {
            const payload = {
                name: form.name.trim(),
                email: form.email.trim(),
                password: form.password,
            };
            for (const [key, value] of Object.entries(form)) {
                if (key === 'name' || key === 'email' || key === 'password') continue;
                if (value !== '' && value !== null && value !== undefined) {
                    if (key === 'age' || key === 'dependents_count') {
                        const num = parseInt(value, 10);
                        if (!isNaN(num)) payload[key] = num;
                    } else {
                        payload[key] = typeof value === 'string' ? value.trim() : value;
                    }
                }
            }
            ok = await register(payload);
        }

        setIsSubmitting(false);
        if (ok) {
            setForm({
                name: '',
                email: '',
                password: '',
                organization: '',
                phone: '',
                age: '',
                gender: '',
                marital_status: '',
                citizenship: '',
                occupation: '',
                employment_status: '',
                annual_income: '',
                address: '',
                country: '',
                state: '',
                city: '',
                pin_code: '',
                smoker_status: '',
                existing_conditions: '',
                emergency_contact_name: '',
                emergency_contact_phone: '',
                education_level: '',
                family_status: '',
                father_name: '',
                mother_name: '',
                disability_status: '',
                critical_illness: '',
                employer: '',
                date_of_birth: '',
                dependents_count: '',
                alcohol_use: '',
                insurance_history: '',
                nominee_name: '',
                nominee_relation: '',
            });
            setShowOptionalProfile(false);
        }
    };

    return (
        <motion.div
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <motion.div
                className="bg-gray-900 border border-gray-700 rounded-2xl p-4 sm:p-6 w-full max-w-5xl max-h-[92vh] overflow-hidden flex flex-col"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
            >
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold">{isLogin ? t('welcomeBack') : t('joinCrux')}</h2>
                    <button onClick={closeLoginModal} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="flex-1 space-y-4 overflow-y-auto pr-1">
                    {!isLogin && (
                        <div>
                            <label htmlFor="signup-name" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-gray-200">
                                <span className="text-red-400">*</span>
                                <span>{t('nameLabel')}</span>
                            </label>
                            <input
                                id="signup-name"
                                name="name"
                                type="text"
                                required
                                placeholder={t('nameLabel')}
                                value={form.name}
                                onChange={handleChange}
                                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                    )}
                    <div>
                        <label htmlFor="signup-email" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-gray-200">
                            <span className="text-red-400">*</span>
                            <span>{t('emailPlaceholder')}</span>
                        </label>
                        <input
                            id="signup-email"
                            name="email"
                            type="email"
                            required
                            placeholder={t('emailPlaceholder')}
                            value={form.email}
                            onChange={handleChange}
                            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                    </div>
                    <div>
                        <label htmlFor="signup-password" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-gray-200">
                            <span className="text-red-400">*</span>
                            <span>{t('passwordPlaceholder')}</span>
                        </label>
                        <input
                            id="signup-password"
                            name="password"
                            type="password"
                            required
                            minLength={8}
                            placeholder={t('passwordPlaceholder')}
                            value={form.password}
                            onChange={handleChange}
                            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                    </div>

                    {!isLogin && (
                        <div className="pt-2 border-t border-gray-700/60">
                            <button
                                type="button"
                                onClick={() => setShowOptionalProfile((prev) => !prev)}
                                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-gray-800/60 hover:bg-gray-800 border border-gray-700/60 text-left transition-colors cursor-pointer"
                            >
                                <div>
                                    <p className="text-sm font-semibold text-gray-200">
                                        Add profile information for better results
                                    </p>
                                    <p className="text-xs text-gray-400 mt-0.5">
                                        Optional — you can complete this later.
                                    </p>
                                </div>
                                {showOptionalProfile ? (
                                    <ChevronUp className="w-5 h-5 text-purple-400 flex-shrink-0" />
                                ) : (
                                    <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                                )}
                            </button>

                            {showOptionalProfile && (
                                <div className="mt-4 space-y-4 pt-2">
                                    <div>
                                        <label htmlFor="signup-organization" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-gray-200">
                                            <span>Organization</span>
                                            <span className="text-xs font-normal text-gray-500">optional</span>
                                        </label>
                                        <input
                                            id="signup-organization"
                                            name="organization"
                                            type="text"
                                            placeholder="Organization"
                                            value={form.organization}
                                            onChange={handleChange}
                                            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        />
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                                        {onboardingFields.map(renderField)}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {authError && <p className="text-sm text-red-400">{authError}</p>}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                    >
                        {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                        {isLogin ? t('signIn') : t('signUp')}
                    </button>

                    <p className="text-center text-gray-400">
                        {isLogin ? t('dontHaveAccount') : t('alreadyHaveAccount')}{' '}
                        <button
                            type="button"
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-purple-400 hover:text-purple-300"
                        >
                            {isLogin ? t('signUp') : t('signIn')}
                        </button>
                    </p>
                </form>
            </motion.div>
        </motion.div>
    );
};

export default AuthModal;
