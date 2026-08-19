/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        'jetbrains-mono': ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float-slow': 'float-slow 15s ease-in-out infinite',
        'float-delayed': 'float-delayed 18s ease-in-out infinite 3s',
        'float-reverse': 'float-reverse 20s ease-in-out infinite 6s',
        'drift-horizontal': 'drift-horizontal 25s linear infinite',
        'drift-horizontal-reverse': 'drift-horizontal-reverse 30s linear infinite 5s',
      },
      keyframes: {
        'float-slow': {
          '0%, 100%': { 
            transform: 'translateY(0px) translateX(0px) scale(1)',
          },
          '25%': { 
            transform: 'translateY(-20px) translateX(10px) scale(1.05)',
          },
          '50%': { 
            transform: 'translateY(-10px) translateX(20px) scale(1.1)',
          },
          '75%': { 
            transform: 'translateY(-30px) translateX(5px) scale(1.05)',
          },
        },
        'float-delayed': {
          '0%, 100%': { 
            transform: 'translateY(0px) translateX(0px) scale(1)',
          },
          '25%': { 
            transform: 'translateY(15px) translateX(-15px) scale(0.95)',
          },
          '50%': { 
            transform: 'translateY(30px) translateX(-10px) scale(0.9)',
          },
          '75%': { 
            transform: 'translateY(10px) translateX(-20px) scale(0.95)',
          },
        },
        'float-reverse': {
          '0%, 100%': { 
            transform: 'translateY(0px) translateX(0px) scale(1)',
          },
          '25%': { 
            transform: 'translateY(25px) translateX(-10px) scale(1.1)',
          },
          '50%': { 
            transform: 'translateY(15px) translateX(-25px) scale(1.15)',
          },
          '75%': { 
            transform: 'translateY(35px) translateX(-5px) scale(1.05)',
          },
        },
        'drift-horizontal': {
          '0%, 100%': { 
            transform: 'translateX(-100px)',
            opacity: '0.1',
          },
          '50%': { 
            transform: 'translateX(100px)',
            opacity: '0.3',
          },
        },
        'drift-horizontal-reverse': {
          '0%, 100%': { 
            transform: 'translateX(100px)',
            opacity: '0.15',
          },
          '50%': { 
            transform: 'translateX(-100px)',
            opacity: '0.25',
          },
        },
      },
    },
  },
  plugins: [
    function({ addUtilities }) {
        const newUtilities = {
            '.animation-delay-4000': {
                'animation-delay': '4000ms',
            },
        }
        addUtilities(newUtilities)
    }
  ],
}