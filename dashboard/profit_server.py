from flask import Flask, request, jsonify
import pandas as pd
import json
import keras
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib

app = Flask(__name__)

def pred_price(max_t):
    print(max_t)
    prices = pd.read_csv('norm_gold_price.csv')['Price'].to_numpy()
    model = keras.saving.load_model('price.keras')
    num_steps_ahead = max_t  # Количество шагов вперед (например, 90 дней или около 3 месяцев)
    sequence_length = 60
    initial_data = prices[-60:]
    input_sequence = initial_data.reshape(1, sequence_length, 1)

    predicted_prices = []

    for _ in range(num_steps_ahead):
        # Предсказание на основе текущей последовательности
        predicted_price = model.predict(input_sequence)
        
        # Добавляем предсказанное значение в список
        predicted_prices.append(predicted_price[0, 0])
        
        # Обновляем входные данные, сдвигая последовательность и добавляя новое предсказание
        input_sequence = np.append(input_sequence[:, 1:, :], [[predicted_price[0]]], axis=1)

    predicted_prices = np.array(predicted_prices)
    return predicted_prices

def pred_profit(volumes, days, T, s, t_prices):
    rate = 0.05 
    scaler_minmax = MinMaxScaler()
    scaler_minmax_risk = MinMaxScaler(feature_range=(-1, 1))
    loaded_model = joblib.load('ebm_profit.joblib')
    profits = []
    for i, day in enumerate(days):
        storage_costs = volumes[i] * (day-np.arange(0, day, 1)) * rate
        product_price = t_prices[:day]
        deal_cost = np.ones(day)*s[i]
        risk = day-np.arange(0, day)-T[i]
        data = pd.DataFrame({
            'product_price': product_price,
            'storage_price': storage_costs,
            'deal_price': deal_cost,
            'risk': risk,  # в процентах (0–1)
        })
        
        data[['product_price', 'storage_price', 'deal_price']] = scaler_minmax.fit_transform(data[['product_price', 'storage_price', 'deal_price']])
        data[['risk']] = scaler_minmax_risk.fit_transform(data[['risk']])
        profit_predictions = loaded_model.predict(data)
        profits.append(profit_predictions.tolist())
    return profits



@app.route('/profit', methods=['POST'])
def profit():
    # Получаем данные из POST запроса
    deals_json = request.get_json()

    # Преобразуем JSON в Python объект (список словарей)
    deals = json.loads(deals_json)

    # Преобразуем в DataFrame
    df = pd.DataFrame(deals)

    predicted_price = pred_price(max(df.day.values))
    print(predicted_price)
    profits = pred_profit(volumes=df.volume, days = df.day, T = df.delivery_time, s =df.price ,t_prices = predicted_price)
    print(profits)
    # Возвращаем ответ
    return jsonify(profits)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
