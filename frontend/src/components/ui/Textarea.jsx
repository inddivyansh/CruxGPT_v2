import React from 'react';

const Textarea = ({ className, ...props }) => (
    <textarea
        className={`w-full px-4 py-3 rounded-lg bg-gray-800/80 border border-gray-700/50 focus:ring-2 focus:ring-purple-500 focus:outline-none focus:border-purple-500 transition-all duration-300 resize-none placeholder-gray-400 text-gray-100 ${className}`}
        {...props}
    ></textarea>
);

export default Textarea;
