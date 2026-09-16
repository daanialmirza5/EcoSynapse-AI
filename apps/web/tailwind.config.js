/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        eco: {
          50: "#f2f8f3",
          100: "#e0efe2",
          200: "#c1dfc6",
          300: "#96c79f",
          400: "#68a874",
          500: "#468a54",
          600: "#356e41",
          700: "#2c5736",
          800: "#26462e",
          900: "#213b28",
        },
      },
    },
  },
  plugins: [],
};
