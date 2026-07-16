# Finch Quant & ML Data API Documentation

This API provides high-performance access to stock price history and financial statements. It is designed to serve data directly to quantitative research environments and machine learning pipelines (such as Google Colab) over local networks or Tailscale.

---

## 🚀 Interactive Documentation (Swagger UI)

FastAPI automatically generates interactive documentation for all endpoints. When the server is running, you can view, test, and explore the schema of all APIs directly in your browser:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (or use your Tailscale IP, e.g., `http://100.xx.xx.xx:8000/docs`)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Endpoints Reference

### 1. Health Check
Verify if the API server is online and check its current environment mode.
- **URL**: `/health`
- **Method**: `GET`
- **Response example (JSON)**:
  ```json
  {
    "status": "ok",
    "production_mode": false
  }
  ```

---

### 2. Get Symbols List
Retrieve all active ticker symbols available in the database.
- **URL**: `/api/symbols`
- **Method**: `GET`
- **Response example (JSON)**:
  ```json
  {
    "symbols": ["AAPL", "MSFT", "YELP", "TSLA"]
  }
  ```

---

### 3. Get Symbol Profile
Retrieve general dimension details (name, sector, industry, country, exchange, asset type, and delisted status) from the database `symbol` table.
- **URL**: `/api/profile/{symbol}`
- **Method**: `GET`
- **Response example (JSON)**:
  ```json
  {
    "name": "Apple Inc. Common Stock",
    "sector": "Technology",
    "industry": "Computer Manufacturing",
    "country": "United States America",
    "exchange": "NASDAQ",
    "asset_type": "stock",
    "delisted": false
  }
  ```

---

### 4. Get Company Info JSON
Fetch the full company metadata profile downloaded from yfinance (containing long business summary, officers, employees, address, etc.).
- **URL**: `/api/info/{symbol}`
- **Method**: `GET`
- **Response example (JSON)**:
  ```json
  {
    "symbol": "AAPL",
    "longName": "Apple Inc.",
    "longBusinessSummary": "Apple Inc. designs, manufactures, and markets smartphones...",
    "website": "https://www.apple.com"
  }
  ```

---

### 5. Get Daily History Prices
Retrieve daily price history for a symbol. Supports custom column selection, date range filtering, and Parquet formatting.
- **URL**: `/api/history/{symbol}`
- **Method**: `GET`
- **Query Parameters**:
  - `start` (Optional): Start date (YYYY-MM-DD), e.g. `2025-01-01`.
  - `end` (Optional): End date (YYYY-MM-DD), e.g. `2026-01-01`.
  - `columns` (Optional): Comma-separated column list to keep, e.g. `Close,Volume`.
  - `format` (Optional): Response format. Either `json` (default) or `parquet`.
- **Response (JSON format)**:
  ```json
  [
    {
      "Date": "2025-01-02 00:00:00",
      "Close": 39.07,
      "Volume": 455300
    }
  ]
  ```
- **Response (Parquet format)**: Returns a raw binary stream of `.parquet` file with the `Date` index and selected columns preserved.

---

### 6. Get Minute History Prices
Retrieve minute-level price history for a symbol.
- **URL**: `/api/minute_history/{symbol}`
- **Method**: `GET`
- **Query Parameters**:
  - `start` (Optional): Start datetime (YYYY-MM-DD HH:MM:SS), e.g. `2026-06-01 09:30:00`.
  - `end` (Optional): End datetime (YYYY-MM-DD HH:MM:SS), e.g. `2026-06-01 16:00:00`.
  - `columns` (Optional): Comma-separated column list, e.g. `Close,Volume`.
  - `format` (Optional): `json` (default) or `parquet`.

---

### 7. Get Financial Statements
Retrieve quarterly financial statements.
- **URL**: `/api/financials/{symbol}/{statement_type}`
- **Method**: `GET`
- **Path Parameters**:
  - `statement_type`: One of `balance_sheet`, `cash_flow`, or `income_stmt`.
- **Query Parameters**:
  - `format` (Optional): `json` (default) or `parquet`.

---

## 🐍 Client Integration Recipes (Python / Pandas)

### Recipe A: Loading Price History using high-performance Parquet format
This is the recommended method for downloading large price history datasets or minute bars. Parquet streaming is up to **10x faster** than JSON parsing and retains exact datatypes and timezones.

```python
import requests
import io
import pandas as pd

def fetch_history_parquet(symbol: str, start: str = None, columns: str = None) -> pd.DataFrame:
    # Replace with your API server's Tailscale or local IP
    api_url = f"http://100.xx.xx.xx:8000/api/history/{symbol}"
    
    params = {
        "format": "parquet"
    }
    if start:
        params["start"] = start
    if columns:
        params["columns"] = columns
        
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        # Load binary bytes directly into Pandas in memory
        df = pd.read_parquet(io.BytesIO(response.content))
        return df
    else:
        raise Exception(f"API Error {response.status_code}: {response.json()}")

# Example Usage:
df = fetch_history_parquet("YELP", start="2025-01-01", columns="Close,Volume")
print(df.head())
```

### Recipe B: Loading JSON Dimension Profiles and metadata
JSON is best suited for fetching metadata, configurations, or company summaries.

```python
import pandas as pd

api_server = "http://100.xx.xx.xx:8000"

# Fetch list of all active symbols
symbols = pd.read_json(f"{api_server}/api/symbols").loc[0, 'symbols']

# Fetch general company dimensions profile
profile = pd.read_json(f"{api_server}/api/profile/AAPL", typ="series")
print(f"Company: {profile['name']}, Sector: {profile['sector']}")
```
