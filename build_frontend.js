const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Directories
const frontendDir = path.join(__dirname, 'frontend');
const outDir = path.join(frontendDir, 'out');

console.log('Building Next.js frontend...');

try {
  // Check if frontend directory exists
  if (!fs.existsSync(frontendDir)) {
    console.error('Error: Frontend directory not found');
    process.exit(1);
  }
  
  // Install necessary dependencies if needed
  console.log('Installing Next.js dependencies...');
  execSync('npm install', { 
    cwd: frontendDir,
    stdio: 'inherit' 
  });
  
  // Build the Next.js application
  console.log('Running Next.js build...');
  execSync('npx next build && npx next export', { 
    cwd: frontendDir,
    stdio: 'inherit' 
  });
  
  console.log('Frontend build completed successfully!');
  console.log(`Output directory: ${outDir}`);
} catch (error) {
  console.error('Build failed:', error.message);
  process.exit(1);
}