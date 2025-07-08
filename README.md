# iRacing Overlays

**iRacing Overlays** is a lightweight desktop application built with **Electron** and **FastAPI**, designed to display real-time telemetry from iRacing in transparent overlay windows.

---

## 📦 Features

- Real-time telemetry (speed, throttle, brake, etc.).
- Fast and responsive: no UI lag, updates every 100ms.
- Transparent always-on-top overlays, styled via HTML/CSS.
- Backend powered by FastAPI with clean API endpoints.
- Frontend rendered using Jinja2 templates and vanilla JavaScript.
- Easily extendable structure with Electron windows per overlay.

---

## 🖼️ Screenshot

---

## 🛠️ Installation

> Requires Python 3.12.0+ and Node.js 18+
```bash
git clone https://github.com/onesch/iracing-overlays.git
cd iracing-overlays

# Python dependencies
pip install -r requirements.txt

# Node dependencies
cd frontend
npm install
```
or install in [releases](https://github.com/onesch/iracing-overlays/releases/tag/publish)

## 🚀 Usage
```bash
# Start FastAPI backend (in one terminal)
uvicorn backend.main:app --reload

# Start Electron app (in another terminal)
npm start
```

## 🗂️ Project Structure

---

## 📌 TODO

---

## 🧑‍💻 Contributing
Pull requests are welcome. Feel free to open issues with suggestions or bug reports.

# 📄 License
[MIT](https://github.com/onesch/iracing-overlays/blob/electron-version/LICENSE) License.
