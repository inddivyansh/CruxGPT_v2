import React from 'react';
import { motion } from 'framer-motion';
import { Linkedin, Github, FileText } from 'lucide-react';
import { useTranslation } from '../contexts/TranslationContext';

const teamMembers = [
    { 
        name: 'Divyansh Nagar', 
        roleKey: 'teamLeadRole', 
        avatar: 'https://placehold.co/128x128/1a1a1a/ffffff?text=DN',
        linkedin: 'https://www.linkedin.com/in/divyansh-nagar-060263344/',
        github: 'https://github.com/inddivyansh',
        resume: 'https://d8it4huxumps7.cloudfront.net/uploads/profileData/files/$%7Bthis.teamId%7D/68774f48d7f6d_divyansh_resume.pdf' // Replace with actual resume link
    },
    { 
        name: 'Manorath Chugh', 
        roleKey: 'backendDevRole', 
        avatar: 'https://placehold.co/128x128/1a1a1a/ffffff?text=MC',
        linkedin: 'https://www.linkedin.com/in/manorath-chugh-b52356353/',
        github: 'https://github.com/manorath295',
        resume: 'https://d8it4huxumps7.cloudfront.net/uploads/profileData/files/28670914/rajaduraimbm12_6878ed229d041.pdf' // Replace with actual resume link
    },
    { 
        name: 'Neel Shroff', 
        roleKey: 'mlEngRole', 
        avatar: 'https://placehold.co/128x128/1a1a1a/ffffff?text=NS',
        linkedin: 'https://www.linkedin.com/in/neel-shroff-7608562a4/',
        github: 'https://github.com/NeelShroff',
        resume: 'https://d8it4huxumps7.cloudfront.net/uploads/profileData/files/28631433/priyankapatel2128_6883201b5e402.pdf' // Replace with actual resume link
    },
    { 
        name: 'Mridul Bansal', 
        roleKey: 'mlDataScientistRole', 
        avatar: 'https://placehold.co/128x128/1a1a1a/ffffff?text=MB',
        linkedin: 'https://www.linkedin.com/in/mridul-bansal-86670a283',
        github: 'https://github.com/MridulBansal-123',
        resume: 'https://d8it4huxumps7.cloudfront.net/uploads/profileData/files/28787045/haarikanuthi115_687bc68a216f2.pdf' // Replace with actual resume link
    },
    { 
        name: 'Mohil Mandape', 
        roleKey: 'mlEngRole', 
        avatar: 'https://placehold.co/128x128/1a1a1a/ffffff?text=MM',
        linkedin: 'https://www.linkedin.com/in/mohil-mandape-6a9638291',
        github: 'https://github.com/MOHILMANDAPE15',
        resume: 'https://d8it4huxumps7.cloudfront.net/uploads/profileData/files/32416755/mohilmandpe33_6801547ecc13d.pdf' // Replace with actual resume link
    },
];

const About = () => {
    const { t } = useTranslation();

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-8 sm:space-y-12">
            <h1 className="text-3xl sm:text-4xl font-bold text-center text-gray-100">{t('aboutTitle')}</h1>
            <p className="text-lg text-gray-400 text-center max-w-3xl mx-auto">{t('aboutDescription')}</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {teamMembers.map((member, index) => (
                <motion.div 
                    key={member.name}
                    className="p-4 sm:p-6 rounded-lg bg-gray-800/50 border border-gray-700/50 text-center hover:bg-gray-800/70 transition-all duration-300"
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                    <img src={member.avatar} alt={member.name} className="w-20 h-20 sm:w-24 sm:h-24 rounded-full mx-auto mb-3 sm:mb-4 border-2 border-purple-400" />
                    <h3 className="text-lg sm:text-xl font-bold text-gray-100">{member.name}</h3>
                    <p className="text-sm sm:text-base text-purple-400 mb-3 sm:mb-4">{t(member.roleKey)}</p>
                    <div className="flex justify-center gap-2 sm:gap-3 mt-3 sm:mt-4">
                        <a 
                            href={member.linkedin} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="p-1.5 sm:p-2 rounded-full bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 hover:text-blue-300 transition-all duration-300"
                            title="LinkedIn Profile"
                        >
                            <Linkedin size={16} className="sm:w-[18px] sm:h-[18px]" />
                        </a>
                        <a 
                            href={member.github} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="p-1.5 sm:p-2 rounded-full bg-gray-600/20 text-gray-400 hover:bg-gray-600/30 hover:text-gray-300 transition-all duration-300"
                            title="GitHub Profile"
                        >
                            <Github size={16} className="sm:w-[18px] sm:h-[18px]" />
                        </a>
                        <a 
                            href={member.resume} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="p-1.5 sm:p-2 rounded-full bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 hover:text-purple-300 transition-all duration-300"
                            title="Resume"
                        >
                            <FileText size={16} className="sm:w-[18px] sm:h-[18px]" />
                        </a>
                    </div>
                </motion.div>
            ))}
        </div>
    </motion.div>
    );
};

export default About;

