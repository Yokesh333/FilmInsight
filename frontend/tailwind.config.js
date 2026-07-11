/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        film: {
          bg:       '#08080F',
          surface:  '#0F0F1A',
          card:     '#151520',
          border:   'rgba(255,255,255,0.06)',
          red:      '#E50914',
          'red-dark':'#B20710',
          gold:     '#F5C518',
          muted:    '#6B7280',
          subtle:   '#9CA3AF',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'Inter', 'sans-serif'],
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #08080F 0%, #0F0F2A 50%, #08080F 100%)',
        'card-gradient': 'linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)',
        'red-gradient':  'linear-gradient(135deg, #E50914 0%, #FF4500 100%)',
        'gold-gradient': 'linear-gradient(135deg, #F5C518 0%, #FFD700 100%)',
      },
      boxShadow: {
        'glow-red':  '0 0 30px rgba(229,9,20,0.3)',
        'glow-gold': '0 0 20px rgba(245,197,24,0.2)',
        'glass':     '0 8px 32px rgba(0,0,0,0.5)',
        'card':      '0 4px 24px rgba(0,0,0,0.4)',
      },
      animation: {
        'shimmer':     'shimmer 2s infinite linear',
        'pulse-slow':  'pulse 3s infinite',
        'float':       'float 6s ease-in-out infinite',
        'glow':        'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%':   { textShadow: '0 0 10px rgba(229,9,20,0.5)' },
          '100%': { textShadow: '0 0 30px rgba(229,9,20,0.9), 0 0 60px rgba(229,9,20,0.4)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
