// Babel configuration used only by Jest (next/babel handles the app build).
// @see https://nextjs.org/docs/pages/building-your-application/configuring/jest
module.exports = {
  presets: [
    ['@babel/preset-env', { targets: { node: 'current' } }],
    ['@babel/preset-react', { runtime: 'automatic' }],
  ],
};
