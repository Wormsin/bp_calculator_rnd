import dash
import numpy as np
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import datetime
import json
import requests  # Для отправки HTTP запросов

# Инициализация Dash приложения
app = dash.Dash(__name__)

# Список для хранения сделок
deals = []

# Layout приложения
app.layout = html.Div([
    # Отступ сверху и шкала времени
    html.Div(style={'padding-top': '30px'}),
    
    # Визуализация временной шкалы с помощью dcc.Slider
    dcc.Slider(
        id='timeline-slider',
        min=0,
        max=150,
        step=1,
        marks={i: str(i) for i in range(0, 151, 10)},  # Шкала от 0 до 150, с метками через 10 дней
        value=0,  # Начальное значение на шкале
        updatemode='drag',  # Обновление значения при перетаскивании ползунка
    ),
    
    # Отступы между полями
    html.Div(style={'padding-top': '20px'}),
    
    # Поля для ввода данных сделки
    html.Div([
        html.Label('Объем товара (кг):'),
        dcc.Input(id='input-volume', type='number', value='', style={'margin-bottom': '10px'}),

        html.Label('Цена сделки (USD):'),
        dcc.Input(id='input-price', type='number', value='', style={'margin-bottom': '10px'}),

        html.Label('Время доставки (дни):'),
        dcc.Input(id='input-delivery-time', type='number', value='', style={'margin-bottom': '10px'}),

        html.Label('Дата сделки:'),
        dcc.Input(id='input-deal-date', type='text', value='', disabled=True),
    ], style={'padding-bottom': '20px'}),  # Отступ между полями ввода

    # Кнопка для назначения сделки
    html.Button('Назначить', id='assign-button', n_clicks=0),
    

    # Вывод данных сделки в консоль
    html.Div(id='deal-data'),

    # Список сделок, который будет обновляться
    html.Div(id='deal-list', style={'padding-top': '20px'}),

    # График для отображения точек на шкале
    dcc.Graph(
        id='timeline',
        config={'staticPlot': False},  # возможность интерактивности
        figure={
            'data': [],
            'layout': go.Layout(
                title='Временная шкала с назначенными сделками',
                xaxis={'range': [0, 150], 'title': 'День', 'showgrid': True},
                yaxis={'showgrid': False, 'zeroline': False, 'visible': False},  # Убираем ось Y
                showlegend=False
            )
        }
    ),

    # Кнопка для отправки сделок на расчет PROFIT
    html.Button('ПРОФИТ', id='profit-button', n_clicks=0),
    # Область для графиков профита
    html.Div(id='profit-graphs', style={'padding-top': '20px'})
])


# Обработчик клика по временной шкале и обновление даты
@app.callback(
    Output('input-deal-date', 'value'),
    Input('timeline-slider', 'value')
)
def update_date(selected_day):
    # Преобразуем номер дня в дату (например, базовая дата - 2024-11-08)
    base_date = datetime.datetime(2024, 11, 8)
    selected_date = base_date + datetime.timedelta(days=int(selected_day))
    return selected_date.strftime('%Y-%m-%d')


# Обработчик назначения сделки с сбросом n_clicks
@app.callback(
    [Output('timeline', 'figure'),
     Output('deal-data', 'children'),
     Output('deal-list', 'children'),
     Output('assign-button', 'n_clicks')],
    Input('assign-button', 'n_clicks'),
    Input('input-volume', 'value'),
    Input('input-price', 'value'),
    Input('input-delivery-time', 'value'),
    Input('input-deal-date', 'value'),
    Input('timeline-slider', 'value')
)
def assign_deal(n_clicks, volume, price, delivery_time, deal_date, selected_day):
    if n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update  # Ничего не делаем, пока не кликнули
    # Добавляем сделку в список
    deals.append({
        'day': selected_day,
        'volume': volume,
        'price': price,
        'delivery_time': delivery_time,
        'deal_date': deal_date
    })


    # Выводим данные сделки в консоль
    print(f"Назначенная сделка: День {selected_day}, Объем: {volume} кг, Цена: {price} USD, Время доставки: {delivery_time} дней, Дата сделки: {deal_date}")

    # Формируем данные для отображения на графике
    deal_markers = []
    for deal in deals:
        deal_marker = {
            'x': [deal['day']],
            'y': [0],  # Ось Y не нужна
            'mode': 'markers',
            'marker': {'symbol': 'triangle-up', 'color': 'blue', 'size': 15},
            'text': [f'Объем: {deal["volume"]} кг\nЦена: {deal["price"]} USD\nДоставка: {deal["delivery_time"]} дней\nДата: {deal["deal_date"]}'],
            'textposition': 'top center'
        }
        deal_markers.append(deal_marker)

    # Создаем фигуру с обновленными треугольниками
    figure = {
        'data': deal_markers,
        'layout': go.Layout(
            title='Временная шкала с назначенными сделками',
            xaxis={'range': [0, 150], 'title': 'День'},
            yaxis={'showgrid': False, 'zeroline': False, 'visible': False},  # Убираем ось Y
            showlegend=False
        )
    }

    # Выводим данные сделки на экран
    deal_info = f"Объем товара: {volume} кг\nЦена сделки: {price} USD\nВремя доставки: {delivery_time} дней\nДата сделки: {deal_date}"

    # Формируем список назначенных сделок
    deal_list = html.Ul([
        html.Li(f"День {deal['day']} - Объем: {deal['volume']} кг, Цена: {deal['price']} USD, Время доставки: {deal['delivery_time']} дней, Дата сделки: {deal['deal_date']}")
        for deal in deals
    ])

    # Сбрасываем n_clicks обратно в 0
    return figure, deal_info, deal_list, 0

'''
# Обработчик для кнопки ПРОФИТ, отправляющий JSON файл
@app.callback(
    Output('profit-button', 'n_clicks'),
    Input('profit-button', 'n_clicks')
)
def handle_profit(n_clicks):
    if n_clicks > 0:
        # Преобразуем список сделок в формат JSON
        deals_json = json.dumps(deals)

        # Отправляем JSON в другой Python скрипт
        response = requests.post('http://localhost:5000/profit', json=deals_json)

        print("Сделки отправлены для расчета PROFIT")

    return dash.no_update
'''

# Обработчик расчета профита и отображения графиков
@app.callback(
    Output('profit-graphs', 'children'),
    Input('profit-button', 'n_clicks')
)
def calculate_profit(n_clicks):
    if n_clicks > 0:
        # Отправка данных на сервер
        deals_json = json.dumps(deals)
        response = requests.post('http://localhost:5000/profit', json=deals_json)
        profit_data = response.json()
        print(profit_data)

        # Создание графиков на основе полученных данных
        graphs = []
        for i, deal_profit in enumerate(profit_data):
            # Создаем график для каждой сделки
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=np.arange(0, deals[i]['day']),
                y=deal_profit,
                mode='lines',
                name=f"Сделка {i}"
            ))
            fig.update_layout(
                title=f"Профит для сделки {i}",
                xaxis_title="Время",
                yaxis_title="Профит"
            )
            graphs.append(dcc.Graph(figure=fig))

        return graphs
    deals.clear()
    return dash.no_update

# Запуск приложения
if __name__ == '__main__':
    app.run_server(debug=True)
