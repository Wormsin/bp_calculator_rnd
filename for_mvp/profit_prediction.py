import joblib
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import numpy as np
import pandas as pd

def calc_profit(df):
    model = joblib.load('ebm_profit_big.joblib')
    
    scaler_profit = joblib.load("scaler_profit.pkl")
    scaler_standard = StandardScaler()
    scaler_minmax = MinMaxScaler()
    
    df[['effective_price', 'total_supplier_price_per_kg']] = scaler_standard.fit_transform(
    df[['effective_price', 'total_supplier_price_per_kg']]
    )
    df[['delivery_cost_per_kg', 'volume']] = scaler_minmax.fit_transform(
    df[['delivery_cost_per_kg', 'volume']]
    )
    profits = []
    plots = {"names": [], "scores":[]}
    
    local_explanations = model.explain_local(df)
    
    names = local_explanations._internal_obj["specific"][0]["names"][:7]
    plots['names'] = names
    
    for i in range(df.shape[0]):
        profit = local_explanations._internal_obj["specific"][i]["perf"]["predicted"]
        profits.append(scaler_profit.inverse_transform(np.array([[profit]]))[0, 0])
        plots['scores'].append(local_explanations._internal_obj["specific"][i]["scores"][:7])
    
    return profits, plots

'''
df = pd.read_csv('profit.csv')
X = df[df.columns[:-1]]
X = X.iloc[:3]
print(calc_profit(X))
'''
    