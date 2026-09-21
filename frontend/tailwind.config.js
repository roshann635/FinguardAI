/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        risk: {
          low: '#16a34a',
          medium: '#d97706',
          high: '#dc2626',
          critical: '#7f1d1d',
        },
        opportunity: '#16a34a',
        action: '#ea580c',
      },
      fontFamily: {
        sans: ['-apple-system', '"Segoe UI"', 'system-ui', 'sans-serif'],
      }
    }
  },
  plugins: []
}
