/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        parchment: '#F5F0E8',
        'parchment-dark': '#EBE3D5',
        ink: '#3E2723',
        'ink-light': '#5D4037',
        jade: '#2E7D32',
        'jade-light': '#4CAF50',
        vermilion: '#C62828',
        cream: '#FFF8E7',
        'cream-dark': '#F5E6CC',
        bamboo: '#8D6E63',
        gold: '#C9A96E',
        'rice-paper': '#FDFBF7',
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', '"Source Han Serif SC"', 'KaiTi', 'STKaiti', '"楷体"', 'serif'],
        sans: ['"Noto Sans SC"', '"Source Han Sans SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
      borderRadius: {
        'callout': '1rem',
      },
    },
  },
  plugins: [],
}
