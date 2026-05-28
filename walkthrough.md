# Forex Tracker — Code Review & Validation

## What the Application Does

This is a modern **Windows desktop GUI application** that tracks the daily **USD → INR "CCY Buy" exchange rate** from **HDFC Bank** and **Axis Bank** and displays it as a beautiful, high-information desktop window.

## GUI Interface Elements

````carousel
![Main GUI Interface](gui_screenshot.png)
<!-- slide -->
![Interactive Hover Tooltip](tooltip_screenshot.png)
````

### Architecture (4 files)

```mermaid
graph LR
    A["scraper.py"] -->|fetches live rates| B["data_manager.py"]
    B -->|stores/reads SQLite| C[(forex_data.db)]
    D["widget_ui.py"] -->|calls| A
    D -->|calls| B
    E["create_startup_shortcut.py"] -->|creates .lnk for| D
```

---

### File-by-File Breakdown

#### 1. [scraper.py](scraper.py) — Web Scraping

| Function | Source | Method |
|---|---|---|
| `get_axis_bank_usd_buy()` | Axis Bank corporate card rate page (HTML) | Fetches the HTML page, parses the `<table>`, finds the USD row, and extracts the **7th numeric value** (index 6) which corresponds to the "CCY BUY" column. |
| `get_hdfc_bank_usd_buy()` | HDFC Bank treasury forex card rates (PDF) | Downloads a PDF, extracts text with `pdfplumber`, finds the line containing `USD` + `UnitedStatesDollar`, and extracts the **7th numeric value** after `USD` — which maps to the "Forex Cards (Cash Out)" rate. A sanity check ensures the rate is between ₹50–₹150. |

Both functions return a `float` on success or `None` on failure.

---

#### 2. [data_manager.py](data_manager.py) — SQLite Persistence

| Function | Purpose |
|---|---|
| `init_db()` | Creates the `rates` table if it doesn't exist. Schema: `(date TEXT, bank TEXT, currency TEXT, rate REAL)` with a unique constraint on `(date, bank, currency)`. |
| `save_rate(bank, currency, rate)` | Inserts today's rate. Uses `INSERT OR REPLACE` so re-fetching on the same day updates the value rather than failing. |
| `get_trend(bank, currency, days=30)` | Returns up to the last 30 days of `(dates, rates)` for graphing. |

The database file path is resolved as an **absolute path** relative to the script's own directory, so it works correctly regardless of the working directory at launch time.

---

#### 3. [widget_ui.py](widget_ui.py) — PyQt6 Desktop GUI

This is the main entry point. It creates a **modern desktop window GUI with standard OS controls** that:

- **Custom USD App Icon**: Loaded directly into the OS title bar next to the window title.
- **Dynamic Resize Auto-Scale**: The trend graph automatically scales and expands vertically to fill the layout when the window is maximized or resized.
- **Interactive Mouse Hover Tooltips**: Displays a snapped vertical indicator line and a highly readable 3-line dark HTML box containing the date, HDFC's rate, and Axis's rate for the hovered coordinate.
- **Dynamic Tooltip Anchoring**: Shifts the tooltip box *below* high spike data points to prevent clipping at the top of the canvas, and *above* low data points.
- **Horizontal 3-Section Footer**: Pins a modern three-column footer at the bottom with a custom stretch distribution of `2:1:1` to prevent text clipping:
  - Left column: Author credit `"Coded by Kaustav Das"` (gray, left-aligned, vertically centered).
  - Center column: Live HDFC daily rate (blue, centered, vertically centered).
  - Right column: Live Axis daily rate (pink, right-aligned, vertically centered).
- **Time-Series Data Alignment**: Aligns HDFC and Axis plot points mathematically by their actual calendar dates on a shared index system.
- **Auto-Refreshes**: Refreshes rate data every **12 hours** via `QTimer`.
- **Background Fetching**: Runs Web scraping tasks on a background `QThread` to keep the UI fluid and responsive.

---

#### 4. [create_startup_shortcut.py](create_startup_shortcut.py) — Windows Startup

Creates a `.lnk` shortcut in the Windows Startup folder pointing to `venv\Scripts\pythonw.exe` (the silent/no-console Python) running `widget_ui.py`. This makes the widget launch automatically on login.

---

## Validation Results

All checks passed ✅

| Check | Result |
|---|---|
| **Syntax** — `py_compile` on all `.py` files | ✅ No errors |
| **Axis Bank scraper** | ✅ Returned `93.82` |
| **HDFC Bank scraper** | ✅ Returned `93.71` |
| **Axis Bank URL reachable** | ✅ HTTP 200 |
| **HDFC Bank URL reachable** | ✅ HTTP 200 |
| **Database init** | ✅ Table created |
| **Database read** | ✅ Returns `(['2026-05-14'], [93.71])` for HDFC |
| **All dependencies importable** | ✅ `PyQt6`, `pyqtgraph`, `requests`, `bs4`, `pdfplumber` |
| **Widget UI launches** | ✅ Opens without errors |

> [!NOTE]
> The scraper relies on **specific HTML/PDF table layouts** from the bank websites. If either bank redesigns their page or changes the column order, the hardcoded index (`rates[6]`) may extract the wrong value or return `None`. This is an inherent fragility of web scraping — something to be aware of but not a bug today.

> [!TIP]
> The `get_trend` query uses `ORDER BY date ASC LIMIT 30`, which returns the **oldest** 30 records, not the **most recent** 30. Once you have more than 30 days of data, the graph will stop showing recent dates. This should be changed to a subquery or `DESC`/reverse approach if you plan to use this long-term. Since you only have 1 day of data currently, it works fine for now.
