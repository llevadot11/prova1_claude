export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          base:   "#0d1117",
          1:      "#161b27",
          2:      "#1e2435",
          3:      "#272e42",
          border: "#2d3548",
        },
        content: {
          primary:   "#e2e8f6",
          secondary: "#8892aa",
          muted:     "#4a5270",
        },
        brand: {
          DEFAULT: "#06b6d4",
          hover:   "#22d3ee",
          dim:     "#0e7490",
        },
        ufi: {
          low:      "#2dd4bf",
          mid:      "#fbbf24",
          high:     "#fb923c",
          critical: "#f87171",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      borderRadius: {
        card: "12px",
        chip: "9999px",
        btn:  "6px",
      },
      backdropBlur: {
        glass: "16px",
      },
      boxShadow: {
        glass:      "0 8px 32px 0 rgba(0,0,0,0.55)",
        "glass-sm": "0 2px 12px 0 rgba(0,0,0,0.35)",
        brand:      "0 0 20px -4px rgba(6,182,212,0.3)",
      },
      animation: {
        "slide-in": "slideIn 0.2s ease-out",
        "fade-in":  "fadeIn 0.15s ease-out",
      },
      keyframes: {
        slideIn: {
          from: { transform: "translateX(12px)", opacity: "0" },
          to:   { transform: "translateX(0)",    opacity: "1" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
