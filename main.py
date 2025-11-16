from fastapi import FastAPI, HTTPException
import pandas as pd
import yfinance as yf

# For CORS add these imports:
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests from your local frontend (or all origins during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # during dev use ["*"]; in prod lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------- Helper Function -----------
def get_stock_data(symbol):
    df = yf.download(symbol, period="1y")

    if df is None or df.empty:
        return None, None, None

    # FIX: Flatten MultiIndex Columns
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    # Reset index
    df.reset_index(inplace=True)

    # Add fields
    df["Daily_Return"] = (df["Close"] - df["Open"]) / df["Open"]
    df["MA_7"] = df["Close"].rolling(7).mean()

    # 52-week stats
    high_52 = df["High"].max()
    low_52 = df["Low"].min()

    return df, high_52, low_52


# ----------- API: Home -----------
@app.get("/")
def home():
    return {"message": "Your Stock API is Running Successfully!"}


# ----------- API: Companies -----------
@app.get("/companies")
def companies():
    return {"available_companies": ["TCS.NS", "INFY.NS", "RELIANCE.NS", "SBIN.NS"]}


# ----------- API: Last 30 days data -----------
@app.get("/data/{symbol}")
def get_data(symbol: str):

    df, high_52, low_52 = get_stock_data(symbol)

    if df is None:
        raise HTTPException(status_code=404, detail="No data found")

    df["date"] = df["Date"].astype(str)
    df = df.where(pd.notnull(df), None)  # replace NaN for JSON

    # Changes made later so that frontend can filter 7-day / 30-day.
    last_30 = df.tail(30)
    return last_30.to_dict(orient="records")
    # return df.to_dict(orient="records")


# ----------- API: Summary -----------
@app.get("/summary/{symbol}")
def summary(symbol: str):

    df, high_52, low_52 = get_stock_data(symbol)

    if df is None:
        raise HTTPException(status_code=404, detail="No data found")

    return {
        "symbol": symbol.upper(),
        "52_week_high": float(high_52),
        "52_week_low": float(low_52),
        "average_close": float(df["Close"].mean())
    }

