# 💵 Forex Tracker Widget

A minimalist, floating Windows desktop widget that tracks the daily **USD → INR "CCY Buy"** exchange rate from **HDFC Bank** and **Axis Bank**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![UI](https://img.shields.io/badge/UI-PyQt6-green)

---

## Features

- Scrapes live USD buy rates from HDFC Bank (PDF) and Axis Bank (HTML)
- Stores daily history in a local SQLite database
- Displays a 30-day trend graph
- Frameless, translucent, always-on-top draggable widget
- Auto-refreshes every 12 hours
- Optional Windows startup shortcut

---

## Prerequisites

- **Windows 10/11**
- **Python 3.10+** installed and added to PATH

---

## Setup & Installation

### 1. Clone the Repository

Open a terminal or command prompt and clone the repository:

```bash
git clone https://github.com/agenticgemini-hub/Forex-Tracker-IND.git
cd Forex-Tracker-IND
```

### 2. Create a Virtual Environment

Create a virtual environment to manage dependencies locally:

* **Windows**:
  ```powershell
  python -m venv venv
  ```
* **macOS/Linux**:
  ```bash
  python3 -m venv venv
  ```

### 3. Activate the Virtual Environment

Activate the environment based on your platform:

* **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate
  ```
* **Windows (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
* **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies

Install the required Python packages:

```bash
pip install PyQt6 pyqtgraph requests beautifulsoup4 pdfplumber
```

> **Optional** — If you want the automatic Windows startup shortcut feature:
> ```powershell
> pip install winshell pywin32
> ```

### 5. Initialize the Database

Initialize the local SQLite database by running:

```bash
python data_manager.py
```

You should see: `Database initialized.`

---

## Running the Widget

### Option A: With Console (for debugging)

```powershell
.\venv\Scripts\Activate
python widget_ui.py
```

### Option B: Silent / No Console Window

```powershell
.\venv\Scripts\pythonw.exe widget_ui.py
```

The widget will appear as a small floating window on your screen.

---

## Usage

| Action | How |
|---|---|
| **Move the widget** | Click and drag anywhere on the widget |
| **Refresh rates** | Click the green **⟳** button |
| **Close the widget** | Click the red **×** button |

---

## Auto-Start on Windows Login (Optional)

Run this once to create a startup shortcut:

```powershell
.\venv\Scripts\Activate
python create_startup_shortcut.py
```

The widget will then launch silently every time you log in.

To **remove** auto-start, delete the shortcut from:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Forex Tracker Widget.lnk
```

---

## Testing the Scraper Independently

You can verify the scraper is working without launching the UI:

```powershell
.\venv\Scripts\Activate
python scraper.py
```

Expected output:
```
Axis Bank USD Buy: 93.82
HDFC Bank USD Buy: 93.71
```

*(Rates will vary by day)*

---

## Project Structure

```
Forex Tracker/
├── widget_ui.py                 # Main entry point — PyQt6 floating widget
├── scraper.py                   # Web scraping for HDFC & Axis Bank rates
├── data_manager.py              # SQLite database operations
├── create_startup_shortcut.py   # Creates Windows startup shortcut
├── forex_data.db                # SQLite database (auto-created)
└── venv/                        # Python virtual environment
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Make sure you activated the venv: `.\venv\Scripts\Activate` |
| Widget not visible | It appears at the top-left corner of your screen — look there first |
| Rates show "Error" | The bank website may be temporarily down. Click ⟳ to retry. |
| Two widgets overlapping | You may have multiple instances running. Check Task Manager for `python.exe` processes. |
