# Transaction Enrichment API
🌐 **Live Demo:** https://web-production-da9a9.up.railway.app

A production-style REST API that enriches bank transactions with category data.
Built with FastAPI and SQLite.

## Tech Stack
- Python 3.9
- FastAPI
- Pydantic v2
- SQLite
- Uvicorn

## Running Locally

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /transactions | Create and enrich a transaction |
| GET | /transactions | Get all transactions |
| GET | /transactions/{id} | Get a single transaction |
| PUT | /transactions/{id} | Update a transaction |
| DELETE | /transactions/{id} | Delete a transaction |
| GET | /health | Health check |

## Auto-categorization

The API automatically categorizes transactions based on description:

| Keyword | Category |
|---------|----------|
| AMAZON | Shopping |
| UBER, CAREEM | Transport |
| NETFLIX, SPOTIFY | Entertainment |
| RESTAURANT, CAFE | Food |
| Everything else | Other |

## Validation

- Description cannot be empty
- Amount must be greater than zero
- Returns 404 when transaction not found

## Example

Request:
```json
{
  "description": "UBER TRIP CAIRO",
  "amount": 85.50
}
```

Response:
```json
{
  "id": 1,
  "description": "UBER TRIP CAIRO",
  "amount": 85.5,
  "category": "Transport"
}
```