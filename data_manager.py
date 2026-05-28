import sqlite3
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "forex_data.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            date TEXT,
            bank TEXT,
            currency TEXT,
            rate REAL,
            UNIQUE(date, bank, currency)
        )
    """)
    conn.commit()
    conn.close()

def save_rate(bank, currency, rate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    today = datetime.date.today().isoformat()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO rates (date, bank, currency, rate)
            VALUES (?, ?, ?, ?)
        """, (today, bank, currency, rate))
        conn.commit()
    except Exception as e:
        print(f"Error saving rate for {bank}: {e}")
    finally:
        conn.close()

def get_trend(bank, currency, days=30):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Get the last 'days' records for the bank and currency, ordered by date ascending
    cursor.execute("""
        SELECT date, rate FROM rates
        WHERE bank = ? AND currency = ?
        ORDER BY date ASC
        LIMIT ?
    """, (bank, currency, days))
    rows = cursor.fetchall()
    conn.close()
    
    dates = [row[0] for row in rows]
    rates = [row[1] for row in rows]
    return dates, rates

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
