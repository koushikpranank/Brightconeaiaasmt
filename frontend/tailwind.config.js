/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f7ff",
          100: "#e0effe",
          200: "#bae0fd",
          300: "#7cc5fb",
          400: "#38a7f6",
          500: "#0e87e3",
          600: "#0269c2",
          700: "#03539e",
          800: "#074782",
          900: "#0c3b6d",
          950: "#082548",
        },
        slate: {
          850: "#131e32",
          900: "#0f172a",
          950: "#070c18",
        },
        emerald: {
          400: "#34d399",
          500: "#10b981",
          950: "#022c22",
        },
        amber: {
          400: "#fbbf24",
          500: "#f59e0b",
          950: "#451a03",
        },
        rose: {
          400: "#fb7185",
          500: "#f43f5e",
          950: "#4c0519",
        },
        cyan: {
          400: "#22d3ee",
          500: "#06b6d4",
          950: "#083344",
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px -5px rgba(14, 135, 227, 0.35)",
        "glow-emerald": "0 0 20px -5px rgba(16, 185, 129, 0.35)",
        "glow-amber": "0 0 20px -5px rgba(245, 158, 11, 0.35)",
        "glow-rose": "0 0 20px -5px rgba(244, 63, 94, 0.35)",
        card: "0 4px 20px -2px rgba(0, 0, 0, 0.25)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 8s linear infinite",
        "fade-in": "fade-in 0.2s ease-out",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: 0, transform: "translateY(2px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

