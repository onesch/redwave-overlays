# iRacing Overlays

**iRacing Overlays** is a lightweight desktop application built with **Electron** and **FastAPI**, designed to display real-time telemetry from iRacing in transparent overlay windows.

![coverage](https://img.shields.io/badge/Version-v1.0.0_dev-blue)
![coverage](https://img.shields.io/badge/Coverage-Required-red)
![version](https://img.shields.io/badge/CodeClimate-А-42f7c0)
![version](https://img.shields.io/badge/Python-3.12.0-blue)
![version](https://img.shields.io/badge/Node.js-18+-blue)
![version](https://img.shields.io/badge/Electron-28.1.0-blue)

## 🖼️ Images

<img width="525" alt="image" src="frontend/static/images/main_window.png" />

## 📦 Features

- Real-time telemetry for iracing.
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
├── backend/                         # FastAPI backend logic.
│   ├── main.py                      # FastAPI entrypoint.
│   │
│   ├── routers/                     # API and views.
│   │   ├── apis.py                  # JSON endpoints.
│   │   └── views.py                 # HTML routes.
│   │
│   ├── services/                    # Business logic modules.
│   │   ├── irsdk/                   # iRacing SDK service.
│   │   │  ├── schemas.py            # Pydantic models (used for validation).
│   │   │  └── service.py            # SDK interaction.
│   │   └── radar/                   # Radar overlay logic.
│   │
│   └── database                     # Local JSON storage.
│       ├── card_desc_database.json  # Card descriptions.
│       ├── data_loader.py           # JSON loader utils.
│       ├── metadata.json            # General metadata.
│       └── overlays_settings.json   # Overlay settings.
│
├── frontend/                        # Electron frontend app.
│   ├── ipc/                         # IPC event handlers (for communication between renderer and main process).
│   │   ├── RadarEvents.js           # Radar window events.
│   │   └── controlsEvents.js        # Controls window events.
│   │
│   ├── static/                      # Static frontend files.
│   │   ├── css/                     # Base and specific styles.
│   │   ├── images/                  # Project images.
│   │   ├── js/                      # Frontend JavaScript (optional).
│   │   └── video/                   # Project videos.
│   │
│   ├── templates/                   # Jinja2 HTML views.
│   │   ├── base/                    # Base and shared components/templates.
│   │   ├── overlays/                # Overlay templates.
│   │   └── pages/                   # Page templates.
│   │
│   ├── utils/                       # Frontend utilities.
│   │   ├── keyboard_protection.js   # Keyboard protection.
│   │   ├── overlay_position.js      # Control overlay position.
│   │   ├── overlay_settings.js      # Control Overlay settings.
│   │   └── overlay_zoom.js          # Control Overlay zoom.
│   │
│   ├── windows/                     # Electron windows logic.
│   │   ├── overlayWindow.js         # Utility to create overlay windows (with routing support).
│   │   └── mainWindow.js            # Logic to create and manage the main Electron window.
│   │
│   ├── main.js                      # Electron entrypoint.
│   └── preload.js                   # Secure preload API.
│
├── LICENSE                          # Project license.
├── README.md                        # Documentation.
├── package-lock.json                # NPM lock file.
├── package.json                     # NPM metadata.
└── requirements.txt                 # Python dependencies (used by pip).
```

## 🧑‍💻 Contributing
Pull requests are welcome. Feel free to open issues with suggestions or bug reports.

# 📄 License
[MIT](https://github.com/onesch/iracing-overlays/blob/electron-version/LICENSE) License.
