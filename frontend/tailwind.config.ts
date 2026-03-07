import type { Config } from 'tailwindcss'

export default {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      spacing: {
        '70': '280px', // Custom width for sidebar
      },
      colors: {
        // Primary brand color (amber/gold) - matching Docusaurus branding
        primary: {
          DEFAULT: '#ffbe00', // Brand color for dark mode
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#ffd966', // lightest from Docusaurus
          400: '#ffbe00', // Original brand color
          500: '#d4a500', // Darker version for light mode
          600: '#bf9400', // dark
          700: '#aa8300', // darker
          800: '#8f6f00', // darkest
          900: '#78350f'
        },
        // Dark theme grays
        gray: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
          950: '#09090b'
        }
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
} satisfies Config

