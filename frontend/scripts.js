const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Build the Next.js app
console.log('Building Next.js application...');
execSync('npx next build && npx next export', {
  cwd: path.resolve(__dirname),
  stdio: 'inherit'
});