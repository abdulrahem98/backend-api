# Transaction Enrichment API

A production-style REST API built with FastAPI that enriches bank transactions with category data.

## Tech Stack
- Python 3.9
- FastAPI
- Pydantic
- Uvicorn

## Running Locally

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic

# Run the API
uvicorn main:app --reload
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /transactions | Enrich a transaction with category |
| GET | /health | Health check |

## Example

Send a transaction:
```json
{
  "description": "AMAZON ORDER 123",
  "amount": 49.99
}
```

Get back enriched data:
```json
{
  "description": "AMAZON ORDER 123",
  "amount": 49.99,
  "category": "Shopping"
}
```