# 🗄️ How to View the Forex Tracker Database

The Forex Tracker application stores its daily exchange rate history in a lightweight, local SQLite database file named `forex_data.db`.

This guide outlines several simple methods you can use to view, query, and inspect the data stored in the `rates` table.

---

## Database Overview
* **Database File**: `forex_data.db` (created automatically in the project folder upon first run).
* **Table Name**: `rates`
* **Schema**:
  * `date` (TEXT): The date of the record in `YYYY-MM-DD` format (e.g., `2026-05-28`).
  * `bank` (TEXT): The source bank (`HDFC` or `Axis`).
  * `currency` (TEXT): The currency code (`USD`).
  * `rate` (REAL): The exchange rate value (e.g., `93.63`).

---

## Method 1: Using a Simple Python Script (Recommended)
You can query the database directly from your terminal using Python. This method is cross-platform and requires no additional software.

1. Activate your virtual environment:
   * **Windows (PowerShell)**: `.\venv\Scripts\Activate`
   * **macOS/Linux**: `source venv/bin/activate`
2. Run the following command to print the database records in a formatted table:

```powershell
python -c "import sqlite3; conn = sqlite3.connect('forex_data.db'); c = conn.cursor(); c.execute('SELECT date, bank, currency, rate FROM rates ORDER BY date DESC'); print(f'{\"Date\":<12} | {\"Bank\":<6} | {\"Currency\":<8} | {\"Rate (Rs)\":<10}'); print('-' * 45); [print(f'{row[0]:<12} | {row[1]:<6} | {row[2]:<8} | {row[3]:<10.2f}') for row in c.fetchall()]; conn.close()"
```

### Sample Output:
```text
Date         | Bank   | Currency | Rate (Rs) 
---------------------------------------------
2026-05-28   | Axis   | USD      | 93.84     
2026-05-28   | HDFC   | USD      | 93.63     
2026-05-27   | Axis   | USD      | 93.84     
```

---

## Method 2: Using a GUI Tool (Visual Browser)
If you prefer a graphical user interface to browse your database without writing code:

1. Download and install **DB Browser for SQLite** (free and open-source) from [sqlitebrowser.org](https://sqlitebrowser.org/).
2. Open DB Browser and click **Open Database**.
3. Select `forex_data.db` from your project folder.
4. Navigate to the **Browse Data** tab to view the `rates` table directly as a spreadsheet.

*(Alternatively, if you are using VS Code, you can install the **SQLite Viewer** or **sqlite** extension to view the `.db` file directly inside the editor).*

---

## Method 3: Using the SQLite Command Line Interface
If you have the `sqlite3` command-line tool installed on your system:

1. Open your terminal in the project directory.
2. Open the database:
   ```bash
   sqlite3 forex_data.db
   ```
3. Set the output formatting for easier reading:
   ```sql
   .headers on
   .mode column
   ```
4. Query the data:
   ```sql
   SELECT * FROM rates ORDER BY date DESC;
   ```
5. Exit the prompt:
   ```sql
   .exit
   ```
