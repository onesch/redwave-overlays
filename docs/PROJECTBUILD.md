[Go back to CONTRIBUTING.md](https://github.com/onesch/redwave-overlays/blob/master/docs/CONTRIBUTING.md)

# ⚡ Project Build Guide

This guide explains how the **RedWave Overlays** project is built, packaged, and executed.  
It is intended for contributors and developers who want to understand the build process or create new builds quickly.

---

## 1. Backend Packaging (FastAPI)

The backend is written in FastAPI and packaged as a single executable using **PyInstaller**.

### 1.1 Build Command
```bash
pyinstaller --onefile --noconsole \
  --icon=frontend/static/images/app_icon.ico \
  --add-data "frontend/templates;frontend/templates" \
  --add-data "frontend/static;frontend/static" \
  --add-data "backend/database/*.json;backend/database" \
  backend/main.py
```
Explanation:
- `--onefile` → creates a single .exe file.
- `--noconsole` → hides the console window.
- `--icon` → sets the application icon.
- `--add-data` → includes templates, static files, and database JSONs.

### 1.2 Post-Build Steps
1. The `main.exe` file is **moved** to root folder(need to create) `backend_run/`  from the `dist/` folder.
2. The `dist/` and `build/` folders from PyInstaller are **deleted** to keep the project clean.

## 2. Frontend Packaging (Electron)
The frontend is an Electron app.

### 2.1 Build Command
```bash
npm run build
```
Explanation:
- Uses electron-builder.
- Creates a `dist/` folder containing a setup .exe.

Notes & Tips:
1. Create a backend build **before** running the `npm run start:prod`.
2. If you need to rebuild Electron, you need to **delete** the `dist/` folder.
3. Installation path for users (default on Windows): ```C:\Users\<User>\AppData\Local\Programs\RedWave overlays```

---

### After these steps, the project is ready for distribution or testing.

---

#### Dev Mode
```npm run start:dev```
- Starts FastAPI backend via uvicorn with --reload.
- Starts Electron in development mode.
- Backend process runs directly, no _MEI folder.
- Useful for testing and development.

#### Production Mode
```npm run start:prod```
- Uses the PyInstaller-built backend executable.
- Electron communicates with the packaged backend.
- Temporary _MEIxxxx folder is used.
- Backend is killed on exit using backendManager.js.
