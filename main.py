from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
import sqlite3

app = FastAPI()

DB_PATH = "transactions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class Transaction(BaseModel):
    description: str
    amount: float

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

def categorize(description: str) -> str:
    description = description.upper()
    if "AMAZON" in description:
        return "Shopping"
    elif "UBER" in description or "CAREEM" in description:
        return "Transport"
    elif "NETFLIX" in description or "SPOTIFY" in description:
        return "Entertainment"
    elif "RESTAURANT" in description or "CAFE" in description:
        return "Food"
    else:
        return "Other"

@app.post("/transactions", status_code=201)
def create_transaction(tx: Transaction):
    category = categorize(tx.description)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (description, amount, category) VALUES (?, ?, ?)",
        (tx.description, tx.amount, category)
    )
    conn.commit()
    tx_id = cursor.lastrowid
    conn.close()
    return {"id": tx_id, "description": tx.description, "amount": tx.amount, "category": category}

@app.get("/transactions")
def get_transactions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, category FROM transactions")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "description": r[1], "amount": r[2], "category": r[3]} for r in rows]

@app.get("/transactions/{tx_id}")
def get_transaction(tx_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, category FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"id": row[0], "description": row[1], "amount": row[2], "category": row[3]}
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
        "UPDATE transactions SET description = ?, amount = ?, category = ? WHERE id = ?",
        (tx.description, tx.amount, category, tx_id)
    )
    conn.commit()
    conn.close()
    return {"id": tx_id, "description": tx.description, "amount": tx.amount, "category": category}

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

@app.get("/health")
def health():
    return {"status": "ok"}
