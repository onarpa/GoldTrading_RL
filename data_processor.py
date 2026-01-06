import pandas as pd
import pandas_ta as ta  # Technical Analysis library

def process_gold_data(file_path):
    # Load and format data (Req 6, 9, 10)
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)
    
    # Cleaning (Req 10)
    df.fillna(method='ffill', inplace=True)
    
    # Feature Engineering: Technical Indicators (Req 11)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    macd = ta.macd(df['Close'])
    df = pd.concat([df, macd], axis=1)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    bbands = ta.bbands(df['Close'], length=20, std=2)
    df = pd.concat([df, bbands], axis=1)
    
    # External Indicators: Mockup (Req 7)
    # In practice, merge with Fed Rates/Dollar Index CSVs here
    df['Fed_Rate'] = 0.05  # Placeholder
    df['USD_Index'] = 104.0 # Placeholder

    return df