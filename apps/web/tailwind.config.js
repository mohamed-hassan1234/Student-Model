/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        graphite: "#374151",
        signal: "#0f766e",
        amberline: "#b45309",
      },
    },
  },
  plugins: [],
};
