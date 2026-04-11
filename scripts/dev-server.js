// scripts/dev-server.js
/**
 * Cross-platform helper to start the LLMLaunchpad backend using the virtual-environment Python.
 * This script works on Windows (".venv\Scripts\python.exe") and on macOS/Linux (".venv/bin/python").
 * It is invoked from the npm script "dev:server": "node scripts/dev-server.js".
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Detect platform – Node reports "win32" on Windows, otherwise it is a Unix-like OS.
const isWindows = process.platform === 'win32';

// Build absolute path to the Python executable inside the venv.
const pythonPath = isWindows
  ? path.join(__dirname, '..', 'server', '.venv', 'Scripts', 'python.exe')
  : path.join(__dirname, '..', 'server', '.venv', 'bin', 'python');

// Check for dev model before starting
const devModelScript = path.join(__dirname, 'get-dev-model.py');
if (fs.existsSync(devModelScript)) {
  console.log('Checking for development model...');
  try {
    execSync(`${pythonPath} "${devModelScript}"`, {
      stdio: 'inherit',
      cwd: path.join(__dirname, '..'),
      env: { ...process.env, LLMLAUNCHPAD_DEV: '1' }
    });
  } catch (e) {
    console.log('Dev model check completed (model may need manual download)');
  }
  console.log('');
}

const serverCwd = path.join(__dirname, '..', 'server');

const child = spawn(pythonPath, ['-m', 'llmlaunchpad'], {
  stdio: 'inherit',
  cwd: serverCwd,
  env: { ...process.env, LLMLAUNCHPAD_DEV: '1' }
});

child.on('close', (code) => {
  // Propagate the exit code to the npm process so that concurrently can detect failures.
  process.exit(code);
});

child.on('close', (code) => {
  // Propagate the exit code to the npm process so that concurrently can detect failures.
  process.exit(code);
});
