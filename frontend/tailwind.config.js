/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        xtractyl: {
          green: '#6baa56',         // primary green
          orange: '#db7127',        // Call-to-Action
          background: '#e6e2cf',    // creme white
          lightgreen: '#9ac48d',    // shiny surfaces
          outline: '#3e3a32',       // outlines
          shadowgreen: '#5b823f',   // depth
          beige: '#cdc0a3',         // box background
          pastelgreen: '#a9c593',   // secondary surfaces
          sand: '#b68956',          // illustrations/Labels
          brown: '#74573a',         // decorative contrast
          offwhite: '#ede6d6',      // background variation
          darktext: '#23211c'       // text on bright surfaces
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif']
        // Optional: dino: ['"Comic Neue"', 'cursive']
      }
    }
  },
  plugins: []
}