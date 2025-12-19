[Go back to CONTRIBUTING.md](https://github.com/onesch/redwave-overlays/blob/master/docs/CONTRIBUTING.md)

# 🗂️ Project Structure
The project is structured to clearly separate frontend and backend logic, making it easier to maintain and extend.

```shell
.
├── backend/                         # FastAPI backend logic.
│   ├── main.py                      # FastAPI entrypoint.
│   │
│   ├── routers/                     # API and views.
│   │   ├── apis.py                  # JSON endpoints.
│   │   └── views/                   # HTML routes.
│   │
│   ├── services/                    # Business logic modules.
│   │   ├── irsdk/                   # iRacing SDK service.
│   │   │  ├── schemas.py            # Pydantic models (used for validation).
│   │   │  ├── service.py            # Connection logic.
│   │   │  └── parser.py             # Telemetry parsing.
│   │   ├── radar/                   # Radar overlay logic.
│   │   └── leaderboard/             # Leaderboard overlay logic.
│   │
│   │
│   ├── utils/                       # Backend utilities.
│   │   ├── paths.py                 # Base path and project path management.
│   │   └── templates.py             # Jinja2 templates for views.
│   │
│   └── database/                    # Local JSON storage.
│       ├── card_desc_database.json  # Card descriptions.
│       ├── data_loader.py           # JSON loader utils.
│       ├── metadata.json            # General metadata.
│       └── overlays_settings.json   # Appears when saving overlays settings.
│
```
```shell
│
├── frontend/                        # Electron frontend app.
│   ├── ipc/                         # IPC event handlers.
│   │
│   ├── static/                      # Static frontend files.
│   │   ├── css/                     # Base and specific styles.
│   │   ├── images/                  # Project images.
│   │   ├── js/                      # Frontend JavaScript.
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
│   │   └── backendManager.js        # Manager backend process.
│   │
│   ├── windows/                     # Electron windows logic.
│   │   ├── overlayWindow.js         # Utility to create overlay windows.
│   │   └── mainWindow.js            # Manage main Electron window.
│   │
│   ├── main.js                      # Electron entrypoint.
│   └── preload.js                   # Secure preload API.
│
```
```shell
├── tests/                           # Project test cases.
├── docs/                           # Project documentation.
│
├── .gitignore                       # Ignored files.
├── LICENSE                          # Project license.
├── README.md                        # Documentation.
├── package-lock.json                # NPM lock file.
├── package.json                     # NPM metadata.
└── requirements.txt                 # Python dependencies (used by pip).
```
