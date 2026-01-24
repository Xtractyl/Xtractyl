/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        xtractyl: {
          white: '#ffffff',          // pure white (tables, data-heavy UI)
          green: '#5b823f',         // primary green (conservative: use as main brand/primary UI)
          orange: '#db7127',        // Call-to-Action / status signal (use sparingly)
          background: '#e6e2cf',    // warm cream background
          lightgreen: '#9ac48d',    // subtle tints / light accents (not dominant)
          outline: '#3e3a32',       // outlines / borders / dividers
          shadowgreen: '#3e3a32',   // conservative depth (avoid “lush” shadows; reuse outline tone)
          beige: '#cdc0a3',         // box background / panels
          pastelgreen: '#a9c593',   // secondary surfaces (large, calm areas)
          sand: '#b68956',          // labels/illustrations (optional, use minimally)
          brown: '#74573a',         // decorative contrast (optional, use minimally)
          offwhite: '#ede6d6',      // background variation (cards/sections)
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