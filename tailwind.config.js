/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./*.{js,ts,jsx,tsx}",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: '#2B2B3D',
        parchment: '#FBF8F1',
        'warm-gray': '#F0ECE3',
        copper: '#C45D30',
        patina: '#5B8C6B',
        rust: '#A0522D',
        slate: '#5A5A72',
        charcoal: '#1A1A2E',
        cream: '#E8C47C',
      },
      fontFamily: {
        display: ['DM Serif Display', 'Georgia', 'serif'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
