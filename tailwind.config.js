/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          500: "#6C63FF",
          700: "#5A53D6",
        },
        accent: "#FF6F61",
      },
      boxShadow: {
        glass: "0 12px 40px rgba(108, 99, 255, 0.18)",
      },
    },
  },
  plugins: [],
};
