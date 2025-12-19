const path = require('path');
const { execFile, exec } = require('child_process');
const http = require('http');

const BACKEND_PORT = 8000;

let backendProcess = null;
let backendStarted = false;


function waitForServer(url, timeout = 15000) {
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      http
        .get(url, () => resolve(true))
        .on('error', () => {
          if (Date.now() - start > timeout) {
            reject(new Error('Backend did not start in time'));
          } else {
            setTimeout(check, 200);
          }
        });
    };

    check();
  });
}

function killBackend(backendProcess, port) {
  if (backendProcess?.pid) {
    exec(`taskkill /PID ${backendProcess.pid} /T /F`);
  }

  const psCommand = `
    Get-NetTCPConnection -LocalPort ${port} -State Listen |
    Select-Object -ExpandProperty OwningProcess |
    ForEach-Object { Stop-Process -Id $_ -Force }
  `;

  exec(
    `powershell -NoProfile -Command "${psCommand.replace(/\n/g, '')}"`,
    (err) => {
      if (err) console.warn(`No backend process found on port ${port}`);
    }
  );
}

async function startBackend() {
  if (backendStarted) return;
  backendStarted = true;

  const exePath = path.join(__dirname, '../../backend_run/main.exe');
  console.log('Starting backend:', exePath);

  backendProcess = execFile(exePath, { windowsHide: true });

  await waitForServer(`http://127.0.0.1:${BACKEND_PORT}`);
  console.log('Backend ready');
}

function stopBackend() {
  console.log('Stopping backend...');
  killBackend(backendProcess, BACKEND_PORT);
}

module.exports = {
  startBackend,
  stopBackend,
};
