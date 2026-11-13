/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        v2: {
          base: 'var(--v2-bg-base)',
          surface: 'var(--v2-bg-surface)',
          control: 'var(--v2-bg-control)',
          border: 'var(--v2-border-subtle)',
          focus: 'var(--v2-border-focus)',
          primary: 'var(--v2-text-primary)',
          secondary: 'var(--v2-text-secondary)',
          muted: 'var(--v2-text-muted)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
