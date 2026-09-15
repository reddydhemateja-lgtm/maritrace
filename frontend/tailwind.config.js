/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#edede9",
          800: "#e3d5ca",
          700: "#f5ebe0",
          600: "#d6ccc2",
        },
        steel: {
          400: "#e6a05c",
          500: "#c97b3f",
          600: "#a8632f",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};