[Go back to CONTRIBUTING.md](https://github.com/onesch/redwave-overlays/blob/master/docs/CONTRIBUTING.md)

# 🗂️ Project Structure
The project is structured to clearly separate frontend and backend logic, making it easier to maintain and extend.

```shell
.
├── backend/                         # FastAPI backend logic.
│   ├── database/                    # Local JSON storage.
│   │   ├── card_desc_database.json  # Card descriptions.
│   │   ├── data_loader.py           # JSON loader utils.
│   │   └── metadata.json            # General metadata.
│   ├── routers/                     # JSON endpoints and HTML routes.
│   ├── services/                    # Business logic modules.
│   ├── utils/                       # Backend utilities.
│   └── main.py                      # FastAPI entrypoint.
│
```
```shell
│
├── frontend/                        # Electron frontend app.
│   ├── ipc/                         # IPC event handlers.
│   ├── static/                      # Frontend static and JavaScript.
│   ├── templates/                   # Jinja2 HTML views.
│   │   ├── base/                    # Base and shared components/templates.
│   │   ├── overlays/                # Overlay templates.
│   │   └── pages/                   # Page templates.
│   ├── utils/                       # Frontend utilities.
│   ├── windows/                     # Electron windows logic.
│   │   ├── overlayWindow.js         # Utility to create overlay windows.
│   │   └── mainWindow.js            # Manage main Electron window.
│   ├── main.js                      # Electron entrypoint.
│   └── preload.js                   # Secure preload API.
│
```
```shell
│
├── docs/                            # Project documentation.
├── tests/                           # Project test cases.
│
├── .gitignore                       # Ignored files.
├── LICENSE                          # Project license.
├── README.md                        # Documentation.
├── package-lock.json                # 
├── package.json                     # NPM metadata.
├── requirements-dev.txt             # 
└── requirements.txt                 # Python dependencies (used by pip).
```
