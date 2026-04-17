/** @type {import('tailwindcss').Config} */
export default {
  content: [
    // 👉 所有源代码：Vue、JS/TS/TSX/JSX
    "./src/**/*.{vue,js,ts,jsx,tsx}",

    // 如果还有其它目录（比如 components/ 或 layouts/ 单独放到根目录）
    // "./components/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
