import React from 'react';

const Button = ({ children, className, variant = 'primary', ...props }) => {
    const baseStyles = "px-6 py-3 rounded-lg font-semibold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black";
    const variants = {
        primary: 'bg-purple-600 text-white hover:bg-purple-700 focus:ring-purple-500',
        secondary: 'bg-gray-700 text-gray-200 hover:bg-gray-600 focus:ring-gray-500',
        danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    };
    return (
        <button className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
            {children}
        </button>
    );
};

export default Button;
