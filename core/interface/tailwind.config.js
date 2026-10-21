/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/pages/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        blue: {
          50: "#f5f3ff", 100: "#ede9fe", 200: "#ddd6fe", 300: "#c4b5fd",
          400: "#a78bfa", 500: "#8b72d9", 600: "#7356c7", 700: "#5f45ad",
          800: "#4c3989", 900: "#3d306d", 950: "#271d49",
        },
        indigo: {
          50: "#f6f3fb", 100: "#eee9f7", 200: "#ddd4ef", 300: "#c5b5e4",
          400: "#a48bd6", 500: "#876bc9", 600: "#7657c9", 700: "#6042b2",
          800: "#4e3790", 900: "#3f2e72", 950: "#281d4b",
        },
      },
    },
  },
  plugins: [],
}
