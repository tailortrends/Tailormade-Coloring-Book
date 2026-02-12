import daisyui from 'daisyui'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Fredoka One', 'Comic Neue', 'cursive'],
        body: ['Nunito', 'Baloo 2', 'sans-serif'],
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '3rem',
      },
      minHeight: {
        tap: '48px', // WCAG touch target minimum
      },
      minWidth: {
        tap: '48px',
      },
    },
  },
  plugins: [daisyui],
  daisyui: {
    themes: [
      {
        tailormade: {
          primary: '#FF6B9D',       // Playful pink
          'primary-content': '#fff',
          secondary: '#4ECDC4',     // Teal
          'secondary-content': '#fff',
          accent: '#FFE66D',        // Sunny yellow
          'accent-content': '#222',
          neutral: '#2D3748',
          'base-100': '#FFFEF7',    // Warm white (not stark white, easy on young eyes)
          'base-200': '#FFF8F0',
          'base-300': '#FFE8D6',
          info: '#7EC8E3',
          success: '#68D391',
          warning: '#F6AD55',
          error: '#FC8181',
        },
      },
      'light',  // Fallback
    ],
    defaultTheme: 'tailormade',
  },
}
