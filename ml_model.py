import numpy as np
from sklearn.ensemble import IsolationForest
import json
import os

CATEGORIES = {
    "AMAZON": "Shopping",
    "NOON": "Shopping",
    "UBER": "Transport",
    "CAREEM": "Transport",
    "NETFLIX": "Entertainment",
    "SPOTIFY": "Entertainment",
    "YOUTUBE": "Entertainment",
    "RESTAURANT": "Food",
    "CAFE": "Food",
    "STARBUCKS": "Food",
    "MCDONALD": "Food",
    "ELECTRICITY": "Utilities",
    "WATER": "Utilities",
    "INTERNET": "Utilities",
    "HOSPITAL": "Healthcare",
    "PHARMACY": "Healthcare",
}

def categorize(description: str) -> str:
    description = description.upper()
    for keyword, category in CATEGORIES.items():
        if keyword in description:
            return category
    return "Other"

def detect_anomaly(amount: float, category: str, history: list) -> dict:
    if len(history) < 3:
        return {"is_anomaly": False, "reason": "Not enough history"}
    
    amounts = np.array([h["amount"] for h in history]).reshape(-1, 1)
    model = IsolationForest(contamination=0.2, random_state=42)
    model.fit(amounts)
    
    prediction = model.predict([[amount]])
    is_anomaly = prediction[0] == -1
    
    avg = np.mean(amounts)
    
    return {
        "is_anomaly": bool(is_anomaly),
        "reason": f"Amount ${amount} is unusual compared to average ${avg:.2f} in {category}" if is_anomaly else "Normal transaction"
    }

def get_spending_summary(transactions: list) -> dict:
    if not transactions:
        return {}
    
    summary = {}
    for tx in transactions:
        cat = tx["category"]
        if cat not in summary:
            summary[cat] = {"total": 0, "count": 0}
        summary[cat]["total"] += tx["amount"]
        summary[cat]["count"] += 1
    
    for cat in summary:
        summary[cat]["average"] = round(summary[cat]["total"] / summary[cat]["count"], 2)
        summary[cat]["total"] = round(summary[cat]["total"], 2)
    
    return summary