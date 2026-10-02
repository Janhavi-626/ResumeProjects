import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: { colors: { ink: "#173b3b", moss: "#42715f", signal: "#c56435" } } },
  plugins: [],
};

export default config;