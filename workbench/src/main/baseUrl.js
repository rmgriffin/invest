import ELECTRON_DEV_MODE from './isDevMode';

// console.log(import.meta.url);
console.log(__dirname)

export default (ELECTRON_DEV_MODE)
  ? 'http://localhost:3000/'
  // : `file://${__dirname}/`;
  : `file://${__dirname}/../`;
