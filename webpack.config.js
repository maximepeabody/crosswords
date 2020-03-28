const path = require('path');

module.exports = {
  entry: './src/simple_app.js',
  output: {
    filename: 'main.js',
    path: path.resolve(__dirname, 'dist'),
  },
};
