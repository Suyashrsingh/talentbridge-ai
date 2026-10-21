/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        purple: {
          50: '#F4F2FF',
          100: '#ECE8FE',
          200: '#DDD5FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#6C4BE8',
          700: '#5A38D4',
          800: '#4C2889',
          900: '#381E69',
        },
        slate: {
          850: '#141824',
          950: '#0B0F19',
        }
      },
      boxShadow: {
        'soft-card': '0 16px 40px -10px rgba(108, 75, 232, 0.09), 0 4px 16px rgba(0, 0, 0, 0.03)',
        'purple-btn': '0 10px 25px -4px rgba(108, 75, 232, 0.45)',
        'purple-glow': '0 0 32px rgba(108, 75, 232, 0.25)',
        'inner-glow': 'inset 0 1px 1px rgba(255, 255, 255, 0.8)',
      },
      animation: {
        'shimmer': 'shimmer 1.8s infinite linear',
        'pulse-subtle': 'pulseSubtle 2.5s infinite ease-in-out',
        'spin-slow': 'spin 4s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '0.9', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.01)' },
        }
      }
    },
  },
  plugins: [],
}
