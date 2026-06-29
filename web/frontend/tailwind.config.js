/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'display': ['Inter', 'Source Sans 3', 'sans-serif'],
        'body': ['Inter', 'Source Sans 3', 'sans-serif'],
      },
      colors: {
        'brand': {
          50: '#fef7ee',
          100: '#fdecd7',
          200: '#fad5ae',
          300: '#f6b77a',
          400: '#f19144',
          500: '#ed7420',
          600: '#de5a16',
          700: '#b84314',
          800: '#933618',
          900: '#772f17',
        },
        'stone': {
          950: '#171412',
        },
        'slate': {
          850: '#172033',
          950: '#0c1322',
        },
      },
      boxShadow: {
        panel: '0 18px 45px rgba(35, 31, 26, 0.08)',
        soft: '0 10px 25px rgba(35, 31, 26, 0.10)',
        orange: '0 12px 24px rgba(237, 116, 32, 0.24)',
        emerald: '0 10px 20px rgba(16, 185, 129, 0.20)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in-right': 'slideInRight 0.28s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(18px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
