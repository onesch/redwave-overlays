# iRacing Overlays

**iRacing Overlays** is a lightweight desktop application built with **Electron** and **FastAPI**, designed to display real-time telemetry from iRacing in transparent overlay windows.

![coverage](https://img.shields.io/badge/Coverage-Required-red)
![version](https://img.shields.io/badge/CodeClimate-А-42f7c0)
![version](https://img.shields.io/badge/Python-3.12.0-blue)
![version](https://img.shields.io/badge/Node.js-18+-blue)
![version](https://img.shields.io/badge/Electron-28.1.0-blue)

## 📦 Features

- Real-time telemetry (speed, throttle, brake, etc.).
- Fast and responsive: no UI lag, updates every 100ms.
- Transparent always-on-top overlays, styled via HTML/CSS.
- Backend powered by FastAPI with clean API endpoints.
- Frontend rendered using Jinja2 templates and vanilla JavaScript.
- Easily extendable structure with Electron windows per overlay.

---

## 🛠️ Installation
```bash
git clone https://github.com/onesch/iracing-overlays.git
cd iracing-overlays

# Python dependencies
pip install -r requirements.txt

# Node dependencies
cd frontend
npm install
```
or install in [releases](https://github.com/onesch/iracing-overlays/releases/tag/publish).

## 🚀 Usage
```bash
# Start FastAPI backend (in one terminal)
uvicorn backend.main:app --reload

# Start Electron app (in another terminal)
npm start
```

## 🗂️ Project Structure

```shell
.
├── backend/                       # Backend logic of the application (FastAPI, services, routing).
│   ├── main.py                    # Entry point for the FastAPI application.
│   │
│   ├── routers/                   # FastAPI route handlers (API and views separation).
│   │   ├── apis.py                # API endpoints (typically return JSON).
│   │   └── views.py               # Page-rendering routes (typically return HTML).
│   │
│   └── services/                  # Business logic and integrations.
│       └── irsdk_service/         # A service module for interacting with iRacing SDK.
│           ├── schemas.py         # Pydantic models (used for validation).
│           └── service.py         # Core logic for communicating with iRSDK.
│
├── frontend/                      # Frontend logic and Electron-related files.
│   ├── ipc/                       # IPC event handlers for communication between renderer and main process.
│   │   ├── controlsEvents.js      # Handles events for the "controls" overlay window.
│   │   └── speedEvents.js         # Handles events for the "speed" overlay window.
│   │
│   ├── static/                    # Static files served to frontend (CSS/JS).
│   │   ├── css/                   # Base and overlay-specific styles.
│   │   ├── images/                # App images.
│   │   └── js/                    # Frontend JavaScript (optional).
│   │
│   ├── templates/                 # Jinja2 HTML templates rendered by FastAPI.
│   │   ├── base/                  # Base and shared components.
│   │   │   ├── base.html          # Main template.
│   │   │   ├── base_overlay.html  # Base template for overlays windows.
│   │   │   └── navigation.html    # Top navigation cards component (included into base.html).
│   │   │
│   │   ├── overlays/              # HTML templates for different overlay windows.
│   │   │
│   │   └── pages/                 # Pages rendered in the main application window.
│   │
│   ├── windows/                   # Logic for creating and managing Electron windows.
│   │   ├── overlayWindow.js       # Utility to create overlay windows (with routing support).
│   │   └── mainWindow.js          # Logic to create and manage the main Electron window.
│   │
│   ├── main.js                    # Entry point for Electron main process.
│   └── preload.js                 # Preload script for securely exposing APIs to renderer.
│
├── LICENSE                        # License file for the project.
├── README.md                      # Project overview and usage instructions.
├── package-lock.json              # NPM dependency lock file.
├── package.json                   # NPM project metadata and dependency list.
└── requirements.txt               # Python dependencies for the backend (used by pip).
```

## 🧑‍💻 Contributing
Pull requests are welcome. Feel free to open issues with suggestions or bug reports.

# 📄 License
[MIT](https://github.com/onesch/iracing-overlays/blob/electron-version/LICENSE) License.
