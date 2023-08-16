module.exports = {
  content: [
    './**/*.{py,_hs}',
    './!(.git|.github|.vscode|.venv|venv|node_modules|__pycache__|.pytest_cache|.weba|weba)/**/*.{py,_hs}',
    '!(__pycache__).{py,_hs}',
  ],
  plugins: [
    require('@tailwindcss/typography'), require('@tailwindcss/aspect-ratio'), require('@tailwindcss/container-queries'),
  ],
}
