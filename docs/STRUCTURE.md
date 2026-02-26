[Go back to CONTRIBUTING.md](https://github.com/onesch/redwave-overlays/blob/master/docs/CONTRIBUTING.md)

# 🗂️ Project Structure
The project is structured to clearly separate frontend and backend logic, making it easier to maintain and extend.

```shell
.
├── backend/                         # FastAPI backend logic.
│   ├── main.py                      # FastAPI entrypoint.
│   │
│   ├── routers/                     # JSON endpoints and HTML routes.
│   │
│   ├── services/                    # Business logic modules.
│   │   ├── base.py                  # Base service implementation.
│   │   ├── irsdk/                   # iRacing SDK Low-level service.
│   │   ├── radar/                   # Radar overlay logic.
│   │   ├── leaderboard/             # Leaderboard overlay logic.
│   │   └── track_map/               # Track map overlay logic.
│   │
│   ├── utils/                       # Backend utilities.
│   │   ├── paths.py                 # Base path and project path management.
│   │   └── templates.py             # Jinja2 templates for views.
│   │
│   └── database/                    # Local JSON storage.
│       ├── card_desc_database.json  # Card descriptions.
│       ├── data_loader.py           # JSON loader utils.
│       └── metadata.json            # General metadata.
│
```
```shell
│
├── frontend/                        # Electron frontend app.
│   ├── ipc/                         # IPC event handlers.
│   │
│   ├── static/                      # Frontend static and JavaScript.
│   │
│   ├── templates/                   # Jinja2 HTML views.
│   │   ├── base/                    # Base and shared components/templates.
│   │   ├── overlays/                # Overlay templates.
│   │   └── pages/                   # Page templates.
│   │
│   ├── utils/                       # Frontend utilities.
│   │   ├── backendManager.js        # Manager backend process.
│   │   ├── overlay_card_opacity.js  # Overlay opacity update logic.
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
```
```shell
│
├── tests/                           # Project test cases.
├── docs/                            # Project documentation.
│
├── .gitignore                       # Ignored files.
├── LICENSE                          # Project license.
├── README.md                        # Documentation.
├── package.json                     # NPM metadata.
└── requirements.txt                 # Python dependencies (used by pip).
```
