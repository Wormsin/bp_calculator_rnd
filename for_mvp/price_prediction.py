import joblib
import pandas as pd
import math 
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

def make_new_data(scaler, df):
    df["Price"] = scaler.transform(df["Price"].to_numpy().reshape((df.shape[0], 1))).T[0]
    window_size = 30
    interval_days = 3
    df['Price_Avg_30'] = df['Price'].rolling(window=window_size).mean()
    df['Price_Std_30'] = df['Price'].rolling(window=window_size).std()
    df['Price_Lag_1'] = df['Price'].shift(-1)
    df['Price_Lag_3'] = df['Price'].shift(-3)
    df['Price_Lag_5'] = df['Price'].shift(-5)

    # Target is 3-day average future price
    df['Future_Price_Avg_3'] = df['Price'].shift(-interval_days).rolling(window=interval_days).mean()
    df.dropna(inplace=True)
    last_data = df[["Price_Avg_30", "Price_Std_30", "Price_Lag_1", "Price_Lag_3", "Price_Lag_5"]].tail(1)
    
    return last_data


def predict_prices(days):
    model = joblib.load('xgboost_model_predict_product_price_3d.joblib')
    
    df = pd.read_csv("original_price.csv")
    df.drop(["Unnamed: 0"], axis=1, inplace=True)
    
    scaler = MinMaxScaler()
    scaler.fit(df.Price.values.reshape(-1,1))
    
    df = df.iloc[-60:][["Price"]]

    price = 0
    prices = np.array([])
    
    for _ in range(math.ceil(days/3)):
        last_data = make_new_data(scaler, df.copy())
        pred_price = model.predict(last_data)
        price = scaler.inverse_transform(np.array([pred_price]))[0, 0]
        prices = np.concat((prices, np.ones(3)*price))
        
        new_rows = pd.DataFrame({'Price': [price, price, price]})
        df = pd.concat([df, new_rows], ignore_index=True)

    return prices

def supplier_prices(start_date, end_date, effective_date, storage, available_from):
    days = (end_date-start_date).days
    supplier_prices = predict_prices(days)*1.2
    if start_date>=available_from:
        start = 0
        max_storage_days = (effective_date-start_date).days
    else:
        start = (available_from-start_date).days
        max_storage_days = (effective_date-available_from).days
    print(max_storage_days)
    storage_price = np.array([storage*d for d in range(max_storage_days, 0, -1)])
    total_supplier_price = np.min(supplier_prices[start:start+max_storage_days]*10+storage_price)
    optimal_time =  np.argmin(supplier_prices[start:start+max_storage_days]*10+storage_price)
    if start==0:
        optimal_date = datetime(start_date.year, start_date.month, start_date.days+optimal_time)
    else:
        optimal_date = datetime(available_from.year, available_from.month, available_from.days+optimal_time)
    
    return supplier_prices, total_supplier_price, optimal_date
