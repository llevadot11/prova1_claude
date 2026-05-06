export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ufi: {
          low: "#22c55e",
          mid: "#f59e0b",
          high: "#ef4444",
          critical: "#7f1d1d",
        },
      },
    },
  },
  plugins: [],
};
