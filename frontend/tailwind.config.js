/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        xtractyl: {
          green: '#6baa56',         // Primärgrün
          orange: '#db7127',        // Call-to-Action
          background: '#e6e2cf',    // Cremeweiß
          lightgreen: '#9ac48d',    // Glanzflächen
          outline: '#3e3a32',       // Konturen
          shadowgreen: '#5b823f',   // Tiefe
          beige: '#cdc0a3',         // Box-Hintergründe
          pastelgreen: '#a9c593',   // Sekundärfläche
          sand: '#b68956',          // Illustrationen/Labels
          brown: '#74573a',         // dekorative Kontraste
          offwhite: '#ede6d6',      // Hintergrundvariation
          darktext: '#23211c'       // Lesetext auf hellen Flächen
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