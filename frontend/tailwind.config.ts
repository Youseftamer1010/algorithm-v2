import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cairo: {
          dark: '#1a1a2e',
          navy: '#16213e',
          blue: '#0f3460',
          accent: '#e94560',
          gold: '#f5c518',
          teal: '#00b4d8',
          green: '#2ecc71',
        }
      }
    },
  },
  plugins: [],
}
export default config
