import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f4ff",
          100: "#e0e9ff",
          200: "#c7d7fe",
          300: "#a4bcfd",
          400: "#7b97fa",
          500: "#5b72f5",
          600: "#3d50ea",
          700: "#2f3dd0",
          800: "#2834a8",
          900: "#1e2578",
          950: "#151a5c",
        },
        navy: {
          50: "#f0f3fa",
          100: "#dde4f2",
          200: "#c2cfe8",
          300: "#9ab0d7",
          400: "#7089c2",
          500: "#4f69b1",
          600: "#3d5297",
          700: "#32427a",
          800: "#2c3867",
          900: "#1e2540",
          950: "#141929",
        },
        slate: {
          850: "#1e2639",
        },
        amber: {
          550: "#f59e0b",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      fontSize: {
        "2xs": "0.625rem",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        "card-hover": "0 4px 6px -1px rgb(0 0 0 / 0.15), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
