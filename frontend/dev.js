const { exec } = require('child_process');
const path = require('path');

// Start the Next.js development server
console.log('Starting Next.js development server...');
const nextProcess = exec('npx next dev -p 3000', {
  cwd: path.resolve(__dirname),
});

nextProcess.stdout.on('data', (data) => {
  console.log(data);
});

nextProcess.stderr.on('data', (data) => {
  console.error(data);
});

nextProcess.on('close', (code) => {
  console.log(`Next.js process exited with code ${code}`);
});