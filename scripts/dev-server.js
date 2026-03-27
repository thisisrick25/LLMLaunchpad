// scripts/dev-server.js
/**
 * Cross‑platform helper to start the LLMLaunchpad backend using the virtual‑environment Python.
 * This script works on Windows (".venv\\Scripts\\python.exe") and on macOS/Linux (".venv/bin/python").
 * It is invoked from the npm script "dev:server": "node scripts/dev-server.js".
 */

const { spawn } = require('child_process');
const path = require('path');

// Detect platform – Node reports "win32" on Windows, otherwise it is a Unix‑like OS.
const isWindows = process.platform === 'win32';

// Build absolute path to the Python executable inside the venv.
const pythonPath = isWindows
  ? path.join(__dirname, '..', 'server', '.venv', 'Scripts', 'python.exe')
  : path.join(__dirname, '..', 'server', '.venv', 'bin', 'python');

// Ensure the path exists (optional sanity check)
// If it does not exist, we still try to spawn – the error will surface.

const serverCwd = path.join(__dirname, '..', 'server');

const child = spawn(pythonPath, ['-m', 'llmlaunchpad'], {
  stdio: 'inherit',
  cwd: serverCwd,
});

child.on('close', (code) => {
  // Propagate the exit code to the npm process so that concurrently can detect failures.
  process.exit(code);
});
