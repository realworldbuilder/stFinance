import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Function to fetch data
def fetch_data(ticker, period='6mo'):
    end_date = datetime.now()
    start_date = datetime(end_date.year, 1, 1) if period == 'ytd' else end_date - timedelta(days=180)  # default to 6 months
    if period == 'max':
        data = yf.download(ticker, period=period)
    else:
        data = yf.download(ticker, start=start_date, end=end_date)
    return data

def add_crossover_annotations(fig, data, row, col):
    # Detect crossovers
    cross_up = (data['EMA_5'] > data['EMA_8']) & (data['EMA_5'].shift(1) < data['EMA_8'].shift(1))
    cross_down = (data['EMA_5'] < data['EMA_8']) & (data['EMA_5'].shift(1) > data['EMA_8'].shift(1))
    # Add annotations
    for date, _ in data[cross_up].iterrows():
        fig.add_annotation(x=date, y=data.loc[date, 'EMA_5'], text='↑', showarrow=True, arrowhead=1, yshift=10, bgcolor='green', font=dict(color='white'), row=row, col=col)
    for date, _ in data[cross_down].iterrows():
        fig.add_annotation(x=date, y=data.loc[date, 'EMA_5'], text='↓', showarrow=True, arrowhead=1, yshift=-10, bgcolor='red', font=dict(color='white'), row=row, col=col)

# Streamlit app layout
st.title('Stock Data with EMA Crossover and RSI')

# Ticker input
ticker = st.text_input('Enter the stock ticker symbol:', 'AAPL')

# Timeframe selection
timeframe = st.selectbox('Select timeframe:', ['1d', '5d', '1mo', '3mo', '6mo', 'ytd', '1y', '5y', 'max'], index=4)

# Fetch the data
data = fetch_data(ticker, timeframe)

if not data.empty:
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
    data['EMA_8'] = data['Close'].ewm(span=8, adjust=False).mean()
    data['EMA_13'] = data['Close'].ewm(span=13, adjust=False).mean()

    # Plotting with subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.2, subplot_titles=(f'{ticker} Candlestick and EMAs', 'RSI'))

    # Add the candlestick plot
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Candlestick'), row=1, col=1)

    # Add EMAs
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_5'], line=dict(color='blue'), name='5 EMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_8'], line=dict(color='orange'), name='8 EMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA_13'], line=dict(color='magenta'), name='13 EMA'), row=1, col=1)

    # Annotate crossovers
    add_crossover_annotations(fig, data, row=1, col=1)

    # RSI plot
    rsi = 100 - (100 / (1 + data['Close'].diff().apply(lambda x: max(x, 0)).rolling(window=14).mean() / data['Close'].diff().apply(lambda x: min(x, 0)).abs().rolling(window=14).mean()))
    fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="Overbought", annotation_position="bottom right", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="Oversold", annotation_position="bottom right", row=2, col=1)

    # Layout adjustments for clear visibility
    fig.update_layout(height=800, title=f'{ticker} Stock Data Analysis',
                      xaxis_rangeslider_visible=True, xaxis_title='', yaxis_title='Price', yaxis2_title='RSI')

    st.plotly_chart(fig)
else:
    st.error("Unable to fetch data. Please check the ticker symbol and try again.")
