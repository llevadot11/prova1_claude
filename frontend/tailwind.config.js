/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: "oklch(0.985 0.005 95)",
          2:       "oklch(0.965 0.006 95)",
          3:       "oklch(0.93  0.008 90)",
        },
        rule: {
          DEFAULT: "oklch(0.82 0.01  85)",
          strong:  "oklch(0.62 0.012 80)",
        },
        ink: {
          DEFAULT: "oklch(0.20 0.015 80)",
          2:       "oklch(0.38 0.012 80)",
          3:       "oklch(0.55 0.01  80)",
        },
        accent: {
          ink: "oklch(0.32 0.05 240)",
        },
        ufi: {
          0: "oklch(0.86 0.06 165)",
          1: "oklch(0.78 0.09 150)",
          2: "oklch(0.84 0.11 95)",
          3: "oklch(0.76 0.14 70)",
          4: "oklch(0.65 0.17 45)",
          5: "oklch(0.48 0.18 30)",
        },
      },
      fontFamily: {
        display: ['"Instrument Serif"', "Georgia", "serif"],
        sans:    ['"Inter Tight"', "Inter", "system-ui", "sans-serif"],
        mono:    ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      fontSize: {
        "display-2xl": ["56px", { lineHeight: "1",    letterSpacing: "-0.01em" }],
        "display-xl":  ["40px", { lineHeight: "1.05", letterSpacing: "-0.005em" }],
        "display-lg":  ["28px", { lineHeight: "1.15" }],
        "body-lg":     ["17px", { lineHeight: "1.5" }],
        "body":        ["14px", { lineHeight: "1.45" }],
        "body-sm":     ["13px", { lineHeight: "1.4" }],
        "caption":     ["11px", { lineHeight: "1.3", letterSpacing: "0.04em" }],
        "mono-lg":     ["24px", { lineHeight: "1" }],
        "mono":        ["13px", { lineHeight: "1.1" }],
      },
      transitionTimingFunction: {
        "out-quart": "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};
