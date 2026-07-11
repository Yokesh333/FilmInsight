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
          bg:        '#07070E',
          surface:   '#0D0D1A',
          card:      '#111120',
          border:    'rgba(255,255,255,0.06)',
          red:       '#E50914',
          'red-dark':'#B20710',
          'red-glow':'rgba(229,9,20,0.25)',
          gold:      '#F5C518',
          'gold-dim':'rgba(245,197,24,0.15)',
          muted:     '#5A6170',
          subtle:    '#9CA3AF',
          dim:       '#374151',
        },
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'Inter', 'sans-serif'],
        mono:    ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'hero-gradient':    'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(229,9,20,0.12) 0%, transparent 60%), linear-gradient(180deg, #07070E 0%, #0A0A15 100%)',
        'card-gradient':    'linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%)',
        'red-gradient':     'linear-gradient(135deg, #E50914 0%, #C8000B 50%, #FF3B21 100%)',
        'red-glow-gradient':'linear-gradient(135deg, rgba(229,9,20,0.8) 0%, rgba(200,0,11,0.8) 100%)',
        'gold-gradient':    'linear-gradient(135deg, #F5C518 0%, #FFD700 100%)',
        'surface-gradient': 'linear-gradient(180deg, #0D0D1A 0%, #07070E 100%)',
        'mesh-gradient':    'radial-gradient(at 20% 50%, rgba(229,9,20,0.06) 0, transparent 50%), radial-gradient(at 80% 20%, rgba(99,102,241,0.05) 0, transparent 50%), radial-gradient(at 50% 80%, rgba(245,197,24,0.04) 0, transparent 50%)',
        'shine':            'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.07) 50%, transparent 60%)',
      },
      boxShadow: {
        'glow-red':   '0 0 40px rgba(229,9,20,0.3), 0 0 80px rgba(229,9,20,0.1)',
        'glow-red-sm':'0 0 20px rgba(229,9,20,0.25)',
        'glow-gold':  '0 0 20px rgba(245,197,24,0.2)',
        'glass':      '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.05)',
        'card':       '0 4px 24px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.04)',
        'card-hover': '0 16px 48px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.08)',
        'button':     '0 4px 16px rgba(229,9,20,0.4), 0 1px 0 rgba(255,255,255,0.1) inset',
        'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.08)',
      },
      animation: {
        'shimmer':      'shimmer 2.2s infinite linear',
        'pulse-slow':   'pulse 3s infinite',
        'float':        'float 6s ease-in-out infinite',
        'glow':         'glow 2.5s ease-in-out infinite alternate',
        'slide-up':     'slideUp 0.5s ease-out',
        'fade-in':      'fadeIn 0.4s ease-out',
        'scale-in':     'scaleIn 0.3s ease-out',
        'border-glow':  'borderGlow 3s ease-in-out infinite alternate',
        'shine':        'shine 3s linear infinite',
        'gradient-x':   'gradientX 4s ease infinite',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-12px)' },
        },
        glow: {
          '0%':   { boxShadow: '0 0 20px rgba(229,9,20,0.2)' },
          '100%': { boxShadow: '0 0 40px rgba(229,9,20,0.5), 0 0 80px rgba(229,9,20,0.2)' },
        },
        slideUp: {
          '0%':   { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: 0 },
          '100%': { opacity: 1 },
        },
        scaleIn: {
          '0%':   { opacity: 0, transform: 'scale(0.95)' },
          '100%': { opacity: 1, transform: 'scale(1)' },
        },
        borderGlow: {
          '0%':   { borderColor: 'rgba(229,9,20,0.2)' },
          '100%': { borderColor: 'rgba(229,9,20,0.6)' },
        },
        shine: {
          '0%':   { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%':      { backgroundPosition: '100% 50%' },
        },
      },
      backdropBlur: {
        xs:  '2px',
        '2xl': '40px',
      },
      borderRadius: {
        '2xl':  '16px',
        '3xl':  '24px',
        '4xl':  '32px',
      },
      transitionTimingFunction: {
        'bounce-soft': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth':      'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
}
