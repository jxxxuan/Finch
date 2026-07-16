import io
import os
import pandas as pd
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from data_loader import FinchDataLoader
from database import create_conn, PRODUCTION
import database.symbol as db_symbol

app = FastAPI(
    title="Finch Quant & ML Data API",
    description="HTTP RESTful API providing high-performance access to stock price history and financial statements.",
    version="1.0.0"
)

# Enable CORS for maximum flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the global data loader
loader = FinchDataLoader()

def serialize_df(df: pd.DataFrame, response_format: str) -> Response:
    """
    Helper function to serialize a Pandas DataFrame into JSON or Parquet binary stream.
    """
    if response_format.lower() == "parquet":
        buffer = io.BytesIO()
        # Keep index (Date/Datetime) inside the Parquet stream
        df.to_parquet(buffer, index=True, engine='pyarrow', compression='zstd')
        return Response(
            content=buffer.getvalue(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=data.parquet"}
        )
    else:
        # Reset index so that Date/Datetime index becomes a column in the JSON response
        index_name = df.index.name or 'Date'
        df_reset = df.reset_index()
        
        # Convert any Datetime/Timestamp columns to string format to prevent JSON serialization errors
        for col in df_reset.columns:
            if pd.api.types.is_datetime64_any_dtype(df_reset[col]):
                df_reset[col] = df_reset[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                
        # Handle potential NaN values by converting them to None so they become null in JSON
        df_reset = df_reset.where(pd.notnull(df_reset), None)
        
        data = df_reset.to_dict(orient="records")
        return data

def filter_df_by_date(df: pd.DataFrame, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    """
    Helper function to filter a DataFrame by start and end dates/times,
    gracefully handling timezone aware/naive mismatches.
    """
    if not start and not end:
        return df

    # Check if index is timezone-aware
    is_tz_aware = df.index.tz is not None

    if start:
        try:
            start_dt = pd.to_datetime(start)
            if is_tz_aware and start_dt.tz is None:
                start_dt = start_dt.tz_localize(df.index.tz)
            elif not is_tz_aware and start_dt.tz is not None:
                start_dt = start_dt.tz_convert(None)
            df = df[df.index >= start_dt]
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start date format: {start}. Error: {str(e)}"
            )

    if end:
        try:
            end_dt = pd.to_datetime(end)
            if is_tz_aware and end_dt.tz is None:
                end_dt = end_dt.tz_localize(df.index.tz)
            elif not is_tz_aware and end_dt.tz is not None:
                end_dt = end_dt.tz_convert(None)
            df = df[df.index <= end_dt]
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid end date format: {end}. Error: {str(e)}"
            )

    return df

@app.get("/health")
def health_check():
    """Health check endpoint to verify API server status."""
    return {"status": "ok", "production_mode": PRODUCTION}

@app.get("/api/symbols")
def get_active_symbols():
    """Retrieve list of active symbols from the database."""
    conn = create_conn()
    try:
        df = db_symbol.get_by_rule(conn, "*", cols=['symbol'])
        return {"symbols": list(df.index)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        conn.close()

@app.get("/api/profile/{symbol}")
def get_symbol_profile(symbol: str):
    """Retrieve general profile details for a given symbol from the database."""
    profile = loader.get_stock_profile(symbol)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Symbol profile not found in database: {symbol}")
    return profile.to_dict()

@app.get("/api/info/{symbol}")
def get_symbol_info(symbol: str):
    """Retrieve the full JSON metadata profile (longBusinessSummary, etc.) for a symbol."""
    try:
        return loader.load_info(symbol)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/history/{symbol}")
def get_daily_history(
    symbol: str,
    start: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    columns: Optional[str] = Query(None, description="Comma-separated column names"),
    format: str = Query("json", description="Response format: 'json' or 'parquet'")
):
    """Retrieve daily price history for a symbol."""
    try:
        df = loader.load_history(symbol)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")

    # 1. Filter by dates (handles timezone mismatches)
    df = filter_df_by_date(df, start, end)

    # 2. Filter by columns
    if columns:
        col_list = [c.strip() for c in columns.split(",") if c.strip()]
        missing_cols = [c for c in col_list if c not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Columns not found: {missing_cols}")
        df = df[col_list]

    return serialize_df(df, format)

@app.get("/api/minute_history/{symbol}")
def get_minute_history(
    symbol: str,
    start: Optional[str] = Query(None, description="Start datetime filter (YYYY-MM-DD HH:MM:SS)"),
    end: Optional[str] = Query(None, description="End datetime filter (YYYY-MM-DD HH:MM:SS)"),
    columns: Optional[str] = Query(None, description="Comma-separated column names"),
    format: str = Query("json", description="Response format: 'json' or 'parquet'")
):
    """Retrieve minute-level price history for a symbol."""
    try:
        df = loader.load_minute_history(symbol)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load minute history: {str(e)}")

    # 1. Filter by dates (handles timezone mismatches)
    df = filter_df_by_date(df, start, end)

    # 2. Filter by columns
    if columns:
        col_list = [c.strip() for c in columns.split(",") if c.strip()]
        missing_cols = [c for c in col_list if c not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Columns not found: {missing_cols}")
        df = df[col_list]

    return serialize_df(df, format)

@app.get("/api/financials/{symbol}/{statement_type}")
def get_financials(
    symbol: str,
    statement_type: str,
    format: str = Query("json", description="Response format: 'json' or 'parquet'")
):
    """Retrieve quarterly financials (balance_sheet, cash_flow, income_stmt)."""
    try:
        df = loader.load_financials(symbol, statement_type)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load financials: {str(e)}")

    return serialize_df(df, format)
