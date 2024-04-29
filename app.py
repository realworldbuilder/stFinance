import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from datetime import datetime, timedelta
import pandas as pd

# Function to fetch data
def fetch_data(ticker, period='6mo'):
    end_date = datetime.now()
    start_date = datetime(end_date.year, 1, 1) if period == 'ytd' else end_date - timedelta(days=180)
    data = yf.download(ticker, start=start_date, end=end_date) if period != 'max' else yf.download(ticker, period='max')
    return data

# Function to add EMAs, calculate RSI, and detect crossovers
def add_indicators_and_find_crossovers(data):
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
    data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()
    data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()

    # RSI Calculation
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # Detect Crossovers with correct direction indications
    data['Crossover'] = ''
    # 5 crosses above 8
    data.loc[(data['EMA_5'] > data['EMA_8']) & (data['EMA_5'].shift(1) < data['EMA_8'].shift(1)), 'Crossover'] = '5 crosses 8 Up'
    # 5 crosses below 8
    data.loc[(data['EMA_5'] < data['EMA_8']) & (data['EMA_5'].shift(1) > data['EMA_8'].shift(1)), 'Crossover'] = '5 crosses 8 Down'
    # 5 crosses above 13
    data.loc[(data['EMA_5'] > data['EMA_13']) & (data['EMA_5'].shift(1) < data['EMA_13'].shift(1)), 'Crossover'] = '5 crosses 13 Up'
    # 5 crosses below 13
    data.loc[(data['EMA_5'] < data['EMA_13']) & (data['EMA_5'].shift(1) > data['EMA_13'].shift(1)), 'Crossover'] = '5 crosses 13 Down'
    return data

# Main application logic
st.title('Stock Data with EMA Crossover and RSI')
ticker = st.text_input('Enter the stock ticker symbol:', 'AAPL')
timeframe = st.selectbox('Select timeframe:', ['1d', '5d', '1mo', '3mo', '6mo', 'ytd', '1y', '5y', 'max'], index=4)
data = fetch_data(ticker, timeframe)

if not data.empty:
    data = add_indicators_and_find_crossovers(data)
    crossovers = data[data['Crossover'] != ''].tail(3).sort_index(ascending=False)

    if not crossovers.empty:
        st.subheader('Last 3 Crossovers')
        for index, row in crossovers.iterrows():
            # Extract information and adjust display order if needed
            description = row['Crossover']
            icon = "⬆️" if "Up" in description else "⬇️"
            date = index.strftime('%Y-%m-%d')
            st.markdown(f"**{date}**: {description} {icon}")

    # Synchronized charts
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, subplot_titles=('Stock Prices and EMAs', 'RSI'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='5 EMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='8 EMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='13 EMA'), row=1, col=1)

    # RSI with overbought and oversold lines
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI'), row=2, col=1)
    fig.add_hline(y=70, line_color="red", line_dash="dash", line_width=1.5, row=2, col=1, annotation_text="Overbought")
    fig.add_hline(y=30, line_color="green", line_dash="dash", line_width=1.5, row=2, col=1, annotation_text="Oversold")

    fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Unable to fetch data. Please check the ticker symbol and try again.")
