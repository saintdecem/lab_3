from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)


class MovingAverageCalculator:
    def calculate_moving_average(self, data, period):
        if len(data) < period:
            return [None] * len(data)
        result = [None] * (period - 1)
        for i in range(period - 1, len(data)):
            result.append(sum(data[i-period+1:i+1]) / period)
        return result

    def forecast(self, data, period, n_days):
        if len(data) < period:
            return [None] * n_days
        forecast_values = []
        extended_data = data.copy()
        for _ in range(n_days):
            extended_data.append(sum(extended_data[-period:]) / period)
            forecast_values.append(extended_data[-1])
        return forecast_values


def analyze_currency(file_path, window_size=5, forecast_periods=7):
    """Загружает Excel, считает статистику и прогноз, возвращает JSON"""
    df = pd.read_excel(file_path)
    
    data = []
    for _, row in df.iterrows():
        date_str = str(row['Date']).split()[0]
        usd_val = float(str(row['RUB_USD']).replace(',', '.'))
        eur_val = float(str(row['RUB_EUR']).replace(',', '.'))
        data.append({'date': date_str, 'usd': usd_val, 'eur': eur_val})
    
    # Статистика
    usd_changes = [data[i]['usd'] - data[i-1]['usd'] for i in range(1, len(data))]
    eur_changes = [data[i]['eur'] - data[i-1]['eur'] for i in range(1, len(data))]
    
    max_usd_gain = max(usd_changes)
    max_usd_loss = min(usd_changes)
    max_eur_gain = max(eur_changes)
    max_eur_loss = min(eur_changes)
    
    gain_day = data[usd_changes.index(max_usd_gain) + 1]['date']
    loss_day = data[usd_changes.index(max_usd_loss) + 1]['date']
    gain_day_eur = data[eur_changes.index(max_eur_gain) + 1]['date']
    loss_day_eur = data[eur_changes.index(max_eur_loss) + 1]['date']
    
    # Прогноз
    calc = MovingAverageCalculator()
    usd_values = [d['usd'] for d in data]
    eur_values = [d['eur'] for d in data]
    
    usd_forecast = calc.forecast(usd_values, window_size, forecast_periods)
    eur_forecast = calc.forecast(eur_values, window_size, forecast_periods)
    
    # Таблица
    table_data = []
    for row in data:
        table_data.append({
            'date': row['date'],
            'usd': round(row['usd'], 2),
            'eur': round(row['eur'], 2)
        })
    
    # Даты прогноза
    last_date = data[-1]['date']
    forecast_dates = []
    date_parts = last_date.split('-')
    day = int(date_parts[2])
    month = int(date_parts[1])
    year = int(date_parts[0])
    for _ in range(forecast_periods):
        day += 1
        forecast_dates.append(f"{year}-{month:02d}-{day:02d}")
    
    forecast = []
    for i in range(forecast_periods):
        forecast.append({
            'date': forecast_dates[i],
            'usd': round(usd_forecast[i], 2),
            'eur': round(eur_forecast[i], 2)
        })
    
    return {
        'table_data': table_data,
        'usd_max_gain': {'value': round(max_usd_gain, 2), 'day': gain_day},
        'usd_max_loss': {'value': round(max_usd_loss, 2), 'day': loss_day},
        'eur_max_gain': {'value': round(max_eur_gain, 2), 'day': gain_day_eur},
        'eur_max_loss': {'value': round(max_eur_loss, 2), 'day': loss_day_eur},
        'forecast': forecast,
        'dates': [d['date'] for d in data],
        'usd_values': usd_values,
        'eur_values': eur_values
    }


@app.route('/process', methods=['POST'])
def process():
    try:
        payload = request.get_json()
        window = int(payload.get('window_size', 5))
        periods = int(payload.get('forecast_periods', 7))
        
        # Ищем файл currency_data.xlsx в папке сервера
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'currency_data.xlsx')
        
        result = analyze_currency(file_path, window, periods)
        return jsonify({'status': 'success', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    print("Сервер Лизы запущен на http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)