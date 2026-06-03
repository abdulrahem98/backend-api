from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Transaction(BaseModel):
    description: str
    amount: float

@app.post("/transactions")
def create_transaction(tx: Transaction):
    category = "Shopping" if "AMAZON" in tx.description.upper() else "Other"
    return {**tx.dict(), "category": category}

@app.get("/health")
def health():
    return {"status": "ok"}

