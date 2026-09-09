/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Legacy brand (kept for backward-compat)
        'brand': {
          50:  '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          900: '#0c4a6e',
        },
        // GIS Command Center palette — muted, enterprise-grade
        'gis': {
          blue:    '#5b7fa6',  // muted slate-blue
          'blue-light': '#dce8f4',
          'blue-dark':  '#3d5a7a',
          sage:    '#7a9e7e',  // sage green
          'sage-light': '#dceede',
          'sage-dark':  '#4e7052',
          slate:   '#7c8fa6',  // mid-slate
          'slate-light': '#e8edf3',
          'slate-dark':  '#3d4f61',
          rose:    '#9b7a84',  // muted rose (for alerts)
          'rose-light': '#f0e4e8',
          amber:   '#a08c5a',  // muted amber
          'amber-light': '#f0e8d4',
          bg:      '#f2f5f8',  // page background
          surface: '#ffffff',
          border:  '#dde3ec',
        },
      },
      fontFamily: {
        sans:   ['Nunito', 'system-ui', 'sans-serif'],
        nunito: ['Nunito', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '24px',
        '4xl': '32px',
      },
      boxShadow: {
        'card':  '0 2px 16px 0 rgba(91,127,166,0.08), 0 1px 3px 0 rgba(60,80,100,0.06)',
        'card-hover': '0 6px 28px 0 rgba(91,127,166,0.14), 0 2px 6px 0 rgba(60,80,100,0.08)',
        'nav':   '0 4px 24px 0 rgba(60,80,110,0.12)',
        'float': '0 8px 32px 0 rgba(60,80,110,0.16)',
      },
      backdropBlur: {
        xs: '4px',
        sm: '8px',
      },
    },
  },
  plugins: [],
}
