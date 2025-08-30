# 🧑‍💻 Contributing Guide

Thanks for your interest in contributing to **iRacing Overlays**!  
This document explains how to set up the project for development.

## 📬 Issues

Feel free to open issues for feature requests, bug reports, or questions.

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

## 🚀 Usage

```bash
# Start FastAPI backend (in one terminal)
uvicorn backend.main:app --reload

# Start Electron app (in another terminal)
npm start
```

## 🧪 Tests
```bash
# Run the full test suite
python -m pytest -vv
```
```bash
# Generate a coverage report
coverage run -m pytest
coverage report -m
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
│   │   │  ├── service.py            # Connection logic.
│   │   │  └── parser.py             # Telemetry parsing.
│   │   └── radar/                   # Radar overlay logic.
│   │
│   └── database                     # Local JSON storage.
│       ├── card_desc_database.json  # Card descriptions.
│       ├── data_loader.py           # JSON loader utils.
│       ├── metadata.json            # General metadata.
│       └── overlays_settings.json   # Overlay settings.
│
├── frontend/                        # Electron frontend app.
│   ├── ipc/                         # IPC event handlers.
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
│   │   ├── overlayWindow.js         # Utility to create overlay windows.
│   │   └── mainWindow.js            # Manage main Electron window.
│   │
│   ├── main.js                      # Electron entrypoint.
│   └── preload.js                   # Secure preload API.
│
├── tests/                           # Project test cases.
│
├── .gitattributes                   # LFS config.
├── .gitignore                       # Ignored files.
├── LICENSE                          # Project license.
├── README.md                        # Documentation.
├── package-lock.json                # NPM lock file.
├── package.json                     # NPM metadata.
└── requirements.txt                 # Python dependencies (used by pip).
```

## ✅ Contribution Workflow

1. Create a new branch from develop:
```bash
git checkout develop
git pull
git checkout -b feature/YOUR_TEXT_HERE
```
2. Make your changes.
3. Run tests to ensure everything works.
4. Open a Pull Request into develop branch.
