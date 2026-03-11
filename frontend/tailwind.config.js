/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
  // Temporarily disable DaisyUI to test pure Tailwind
  // plugins: [require('daisyui')],
  // daisyui: {
  //   themes: ["light"],
  //   base: true,
  //   styled: true,
  //   utils: true,
  // },
}
