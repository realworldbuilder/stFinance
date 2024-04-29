import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd

# Function to fetch data
def fetch_data(ticker, period='6mo'):
    end_date = datetime.now()
    start_date = datetime(end_date.year, 1, 1) if period == 'ytd' else end_date - timedelta(days=180)  # default to 6 months
    if period == 'max':
        data = yf.download(ticker, period=period)
    else:
        data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Function to detect crossovers and create a DataFrame
def get_crossovers(data):
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
    data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()
    cross_up = (data['EMA_5'] > data['EMA_8']) & (data['EMA_5'].shift(1) < data['EMA_8'].shift(1))
    cross_down = (data['EMA_5'] < data['EMA_8']) & (data['EMA_5'].shift(1) > data['EMA_8'].shift(1))
    crossovers = pd.DataFrame({
        'Date': data[cross_up | cross_down].index,
        'Price at Crossover': data['Close'][cross_up | cross_down],
        'EMA_5': data['EMA_5'][cross_up | cross_down],
        'EMA_8': data['EMA_8'][cross_up | cross_down],
        'Crossover Type': ['Up' if x else 'Down' for x in cross_up[cross_up | cross_down]]
    })
    return crossovers

# Streamlit app layout
st.title('Stock Data with EMA Crossover and RSI')

# Ticker input
ticker = st.text_input('Enter the stock ticker symbol:', 'AAPL')

# Timeframe selection
timeframe = st.selectbox('Select timeframe:', ['1d', '5d', '1mo', '3mo', '6mo', 'ytd', '1y', '5y', 'max'], index=4)

# Fetch the data
data = fetch_data(ticker, timeframe)

if not data.empty:
    # Calculate EMAs
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
    data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()
    data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()

    # Plotting
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=(f'{ticker} Prices and EMAs', 'RSI'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], mode='lines', name='5 EMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], mode='lines', name='8 EMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], mode='lines', name='13 EMA'), row=1, col=1)

    # RSI calculation and plot
    rsi = 100 - (100 / (1 + data['Close'].diff().apply(lambda x: max(x, 0)).rolling(window=14).mean() / data['Close'].diff().apply(lambda x: min(x, 0)).abs().rolling(window=14).mean()))
    fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="Overbought", annotation_position="bottom right", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="Oversold", annotation_position="bottom right", row=2, col=1)

    # Update layout
    fig.update_layout(height=800, title=f'{ticker} Stock Data Analysis')
    st.plotly_chart(fig)

    # Get crossovers and display last 5
    crossovers = get_crossovers(data)
    last_5_crossovers = crossovers.tail(5)
    st.subheader('Last 5 EMA Crossovers')
    st.dataframe(last_5_crossovers)

else:
    st.error("Unable to fetch data. Please check the ticker symbol and try again.")
