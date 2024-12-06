import pandas as pd
import yfinance as yf
import math

def get_user_input_from_csv(file_path):
    # Read the CSV file containing stock symbols and weightages
    stock_data = pd.read_csv(file_path)
    
    # List all stocks and their weightages
    print("\nAvailable stocks and their weightages:")
    print(stock_data[['Ticker', 'Weightage']])
    
    # Get user selection of stocks to invest in
    selected_stocks = input("Enter the stock symbols to invest in, separated by commas (e.g., BPCL, TCS): ")
    selected_stocks = selected_stocks.split(",")
    
    # Add ".NS" to the stock symbols for NSE (Indian stocks)
    selected_stocks = [stock.strip() + ".NS" for stock in selected_stocks]
    
    # Get the total investment amount and date range from user input
    investment_amount = float(input("Enter total investment amount: "))
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    
    # Get the weightages of selected stocks
    selected_weights = stock_data[stock_data['Ticker'].isin([stock[:-3] for stock in selected_stocks])]
    selected_weights = dict(zip(selected_weights['Ticker'], selected_weights['Weightage']*10))

    return investment_amount, start_date, end_date, selected_stocks, selected_weights
def fetch_stock_data(stock, start_date, end_date):
    # Fetch stock data from Yahoo Finance using Ticker
    stock_data = yf.Ticker(stock)
    data = stock_data.history(start=start_date, end=end_date)
    
    # Remove Dividends and Stock Splits columns
    del data["Dividends"]
    del data["Stock Splits"]
    
    return data

def calculate_rsi(data, period=14):
    
    # Calculate daily price changes
    delta = data['Close'].diff()

    # Separate gains and losses
    gain = (delta.where(delta > 0, 0))  # Keep only positive changes
    loss = (-delta.where(delta < 0, 0))  # Keep only negative changes

    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    return rsi

def adjust_weightage(rsi_value, weightage):
    # Adjust weightage based on RSI value
    if rsi_value > 90:
        return weightage * 0.7  # Reduce by 30%
    elif rsi_value > 80:
        return weightage * 0.8  # Reduce by 20%
    elif rsi_value > 70:
        return weightage * 0.9  # Reduce by 10%
    elif rsi_value < 30:
        return weightage * 1.3  # Increase by 30%
    elif rsi_value < 20:
        return weightage * 1.2  # Increase by 20%
    elif rsi_value < 10:
        return weightage * 1.1  # Increase by 10%
    else:
        return weightage

def main():
    # Step 1: Get user inputs from CSV file
    file_path = 'Stocks.csv'
    investment_amount, start_date, end_date, selected_stocks, selected_weights = get_user_input_from_csv(file_path)

    # Step 2: Calculate the total weightage of selected stocks
    total_weightage = sum(selected_weights.values())
    
    # Normalize the weights so that they sum up to 1 (100%)
    normalized_weights = {stock: weight / total_weightage for stock, weight in selected_weights.items()}

    # Step 3: Process each selected stock
    total_investment = 0
    for stock, weightage in normalized_weights.items():
        stock_symbol = stock + ".NS"  # Append ".NS" for NSE-listed stocks
        print(f"\nProcessing {stock_symbol}...")

        # Fetch stock data
        data = fetch_stock_data(stock_symbol, start_date, end_date)
        
        # Calculate RSI using the provided function
        data['RSI'] = calculate_rsi(data, period=14)

        # Calculate the investment amount for this stock
        stock_investment = weightage * investment_amount
        total_investment += stock_investment
        # Calculate the number of shares to buy based on adjusted weightage (rounded down to whole numbers)
        data['Investment'] = stock_investment
        data['Shares'] = (data['Investment'] / data['Close']).apply(math.floor)
        
        # Adjust investment based on RSI for each day
        data['Adjusted Shares'] = data.apply(lambda row: math.floor(row['Investment'] / row['Close']) 
                                              if row['RSI'] > 70 
                                              else row['Shares'], axis=1)

        # Print adjusted shares per day
        print(f"\nAdjusted Investment and Shares for {stock_symbol}:")
        print(data[['Close', 'RSI', 'Shares', 'Adjusted Shares']])

    # Display total investment allocation
    print(f"\nTotal Investment Allocated: {total_investment}")
    
if __name__ == "__main__":
    main()
