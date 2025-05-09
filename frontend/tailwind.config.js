/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          primary: {
            DEFAULT: '#4F46E5',
            light: '#6366F1',
            dark: '#3730A3',
          },
          secondary: {
            DEFAULT: '#10B981',
          },
          dark: {
            'bg': '#111827',
            'surface': '#1F2937',
            'border': '#374151',
            'text-primary': '#F9FAFB',
            'text-secondary': '#D1D5DB',
          }
        },
        fontFamily: {
          sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', '"Noto Sans"', 'sans-serif'],
          mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
        },
      },
    },
    plugins: [],
  }