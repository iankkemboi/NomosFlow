import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-page":    "#F9F7F2",
        "bg-card":    "#FFFFFF",
        "bg-sidebar": "#F2EFE9",
        "border-card":"#E8E4DC",
        "text-primary":   "#1A1A1A",
        "text-secondary": "#6B6860",
        "text-muted":     "#A09D97",
        "accent-green":        "#3D6B2C",
        "accent-green-light":  "#EBF2E6",
        "risk-critical": "#DC2626",
        "risk-high":     "#EA580C",
        "risk-medium":   "#CA8A04",
        "risk-low":      "#16A34A",
        "status-paid":     "#16A34A",
        "status-failed":   "#DC2626",
        "status-retrying": "#2563EB",
        "status-pending":  "#CA8A04",
      },
      fontFamily: {
        heading: ["Lora", "Georgia", "serif"],
        body:    ["Inter", "sans-serif"],
      },
      borderRadius: {
        card: "12px",
        pill: "9999px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
