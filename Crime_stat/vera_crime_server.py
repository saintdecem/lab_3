from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)


def analyze_crime(file_path, window_size=3, forecast_periods=3):
    df = pd.read_excel(file_path)
    
    column_map = {}
    possible_names = {
        'year': ['year', 'god', 'let'],
        'murder': ['murder', 'murders', 'ubiystva'],
        'robbery': ['robbery', 'robberies', 'razboi'],
        'theft': ['theft', 'thefts', 'krazha'],
        'fraud': ['fraud', 'trickery', 'moshennichestvo'],
        'drugs': ['drugs', 'drug', 'narkotiki'],
        'economic': ['economic', 'economy', 'ekonomicheskie']
    }
    
    for col in df.columns:
        col_lower = str(col).strip().lower()
        for key, names in possible_names.items():
            if key not in column_map:
                for name in names:
                    if name in col_lower:
                        column_map[key] = col
                        break
    
    fields = ['year', 'murder', 'robbery', 'theft', 'fraud', 'drugs', 'economic']
    
    data = []
    for _, row in df.iterrows():
        record = {}
        for key in fields:
            val = row[column_map[key]]
            if isinstance(val, str):
                val = val.replace(',', '.')
            record[key] = float(val) if key != 'year' else int(float(val))
        data.append(record)
    
    table_data = []
    for row in data:
        table_data.append({
            'year': row['year'],
            'murder': row['murder'],
            'robbery': row['robbery'],
            'theft': row['theft'],
            'fraud': row['fraud'],
            'drugs': row['drugs'],
            'economic': row['economic']
        })
    
    first = data[0]
    last = data[-1]
    changes = {}
    for field in ['murder', 'robbery', 'theft', 'fraud', 'drugs', 'economic']:
        if first[field] != 0:
            changes[field] = ((last[field] - first[field]) / first[field]) * 100
    
    most_decreased = min(changes, key=changes.get)
    most_increased = max(changes, key=changes.get)
    
    names = {
        'murder': 'Murder', 'robbery': 'Robbery', 'theft': 'Theft',
        'fraud': 'Fraud', 'drugs': 'Drugs', 'economic': 'Economic'
    }
    
    forecast = {}
    for field in fields[1:]:
        values = [d[field] for d in data]
        working = values.copy()
        field_forecast = []
        for _ in range(forecast_periods):
            avg = sum(working[-window_size:]) / window_size
            field_forecast.append(round(avg, 2))
            working.append(avg)
        forecast[field] = field_forecast
    
    last_year = data[-1]['year']
    forecast_years = list(range(last_year + 1, last_year + forecast_periods + 1))
    
    forecast_data = []
    for i, year in enumerate(forecast_years):
        row = {'year': year}
        for field in fields[1:]:
            row[field] = forecast[field][i]
        forecast_data.append(row)
    
    return {
        'table_data': table_data,
        'years': [d['year'] for d in data],
        'fields': fields[1:],
        'values': {f: [d[f] for d in data] for f in fields[1:]},
        'most_decreased': {'name': names[most_decreased], 'value': round(changes[most_decreased], 1)},
        'most_increased': {'name': names[most_increased], 'value': round(changes[most_increased], 1)},
        'changes': {names[k]: round(v, 1) for k, v in changes.items()},
        'forecast': forecast_data
    }


@app.route('/process', methods=['POST'])
def process():
    try:
        payload = request.get_json()
        window = int(payload.get('window_size', 3))
        periods = int(payload.get('forecast_periods', 3))
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'crime_data.xlsx')
        
        result = analyze_crime(file_path, window, periods)
        return jsonify({'status': 'success', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    print("Server running at http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001)