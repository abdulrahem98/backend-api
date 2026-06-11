from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
import sqlite3
from ml_model import categorize, detect_anomaly, get_spending_summary
from datetime import date

app = FastAPI(title="Smart Finance Tracker")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

DB_PATH = "finance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            is_anomaly INTEGER DEFAULT 0,
            anomaly_reason TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    default_categories = ["Shopping", "Transport", "Entertainment", "Food", "Utilities", "Healthcare", "Other"]
    for cat in default_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    conn.commit()
    conn.close()

init_db()

class Transaction(BaseModel):
    description: str
    amount: float
    date: str = str(date.today())
    category_override: str = ""

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

@app.post("/transactions", status_code=201)
def create_transaction(tx: Transaction):
    category = categorize(tx.description) if not tx.category_override else tx.category_override
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM transactions WHERE category = ?", (category,))
    history = [{"amount": row[0]} for row in cursor.fetchall()]
    anomaly = detect_anomaly(tx.amount, category, history)
    cursor.execute(
        "INSERT INTO transactions (description, amount, category, date, is_anomaly, anomaly_reason) VALUES (?, ?, ?, ?, ?, ?)",
        (tx.description, tx.amount, category, tx.date, int(anomaly["is_anomaly"]), anomaly["reason"])
    )
    conn.commit()
    tx_id = cursor.lastrowid
    conn.close()
    return {
        "id": tx_id,
        "description": tx.description,
        "amount": tx.amount,
        "category": category,
        "date": tx.date,
        "anomaly": anomaly
    }

@app.get("/transactions")
def get_transactions(month: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if month:
        cursor.execute(
            "SELECT id, description, amount, category, date, is_anomaly, anomaly_reason FROM transactions WHERE strftime('%Y-%m', date) = ?",
            (month,)
        )
    else:
        cursor.execute("SELECT id, description, amount, category, date, is_anomaly, anomaly_reason FROM transactions")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "description": r[1], "amount": r[2], "category": r[3], "date": r[4], "is_anomaly": bool(r[5]), "anomaly_reason": r[6]} for r in rows]

@app.get("/transactions/{tx_id}")
def get_transaction(tx_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, category, date, is_anomaly, anomaly_reason FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"id": row[0], "description": row[1], "amount": row[2], "category": row[3], "date": row[4], "is_anomaly": bool(row[5]), "anomaly_reason": row[6]}

@app.put("/transactions/{tx_id}")
def update_transaction(tx_id: int, tx: Transaction):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transactions WHERE id = ?", (tx_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Transaction not found")
    category = categorize(tx.description)
    cursor.execute(
        "UPDATE transactions SET description = ?, amount = ?, category = ?, date = ? WHERE id = ?",
        (tx.description, tx.amount, category, tx.date, tx_id)
    )
    conn.commit()
    conn.close()
    return {"id": tx_id, "description": tx.description, "amount": tx.amount, "category": category, "date": tx.date}

@app.delete("/transactions/{tx_id}", status_code=204)
def delete_transaction(tx_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transactions WHERE id = ?", (tx_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Transaction not found")
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()

@app.get("/summary")
def get_summary(month: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if month:
        cursor.execute(
            "SELECT amount, category FROM transactions WHERE strftime('%Y-%m', date) = ?",
            (month,)
        )
    else:
        cursor.execute("SELECT amount, category FROM transactions")
    rows = cursor.fetchall()
    conn.close()
    transactions = [{"amount": r[0], "category": r[1]} for r in rows]
    return get_spending_summary(transactions)

@app.get("/anomalies")
def get_anomalies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, category, date, anomaly_reason FROM transactions WHERE is_anomaly = 1")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "description": r[1], "amount": r[2], "category": r[3], "date": r[4], "reason": r[5]} for r in rows]

@app.get("/categories")
def get_categories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

@app.post("/categories", status_code=201)
def add_category(payload: dict):
    name = payload.get("name", "").strip().title()
    if not name:
        raise HTTPException(status_code=400, detail="Category name cannot be empty")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Category already exists")
    conn.close()
    return {"name": name}

@app.get("/months")
def get_months():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT strftime('%Y-%m', date) as month FROM transactions ORDER BY month DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

@app.get("/health")
def health():
    return {"status": "ok"}