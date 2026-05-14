async function sendToBackend(port, payload) {
    const url = `http://127.0.0.1:${port}/process`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`Ошибка: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Сервер недоступен:', error);
        alert(`Не удалось подключиться к серверу на порту ${port}. Проверьте, что сервер запущен.`);
        return null;
    }
}

// === Функции для вкладки Лизы (валюта) ===

let currencyChart = null;
let currencyForecastChart = null;

async function loadCurrency() {
    const windowSize = parseInt(document.getElementById('currencyWindowSize')?.value || 5);
    const forecastPeriods = parseInt(document.getElementById('currencyForecastPeriods')?.value || 7);

    const result = await sendToBackend(5000, {
        window_size: windowSize,
        forecast_periods: forecastPeriods
    });

    if (!result || result.status !== 'success') return;

    // Таблица
    let html = '<table><tr><th>Дата</th><th>USD/RUB</th><th>EUR/RUB</th></tr>';
    result.table_data.forEach(row => {
        html += `<tr><td>${row.date}</td><td>${row.usd}</td><td>${row.eur}</td></tr>`;
    });
    html += '</table>';
    document.getElementById('currencyTable').innerHTML = html;

    // Статистика
    const usdGain = result.usd_max_gain;
    const usdLoss = result.usd_max_loss;
    const eurGain = result.eur_max_gain;
    const eurLoss = result.eur_max_loss;

    document.getElementById('currencyStats').innerHTML = `
        <div class="stats-box">
            USD: ▲ +${usdGain.value} руб (${usdGain.day}) | ▼ ${usdLoss.value} руб (${usdLoss.day})<br>
            EUR: ▲ +${eurGain.value} руб (${eurGain.day}) | ▼ ${eurLoss.value} руб (${eurLoss.day})
        </div>
    `;

    // Основной график
    const ctx = document.getElementById('currencyChart').getContext('2d');
    if (currencyChart) currencyChart.destroy();

    currencyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: result.dates,
            datasets: [
                {
                    label: 'USD/RUB',
                    data: result.usd_values,
                    borderColor: '#2962ff',
                    tension: 0.3
                },
                {
                    label: 'EUR/RUB',
                    data: result.eur_values,
                    borderColor: '#d32f2f',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Курс рубля к USD и EUR' }
            }
        }
    });

    // График прогноза
    const forecastDates = result.forecast.map(f => f.date);
    const forecastUsd = result.forecast.map(f => f.usd);
    const forecastEur = result.forecast.map(f => f.eur);

    const ctxF = document.getElementById('currencyForecastChart').getContext('2d');
    if (currencyForecastChart) currencyForecastChart.destroy();

    currencyForecastChart = new Chart(ctxF, {
        type: 'line',
        data: {
            labels: forecastDates,
            datasets: [
                {
                    label: 'USD (прогноз)',
                    data: forecastUsd,
                    borderColor: '#2962ff',
                    borderDash: [5, 5],
                    tension: 0.3
                },
                {
                    label: 'EUR (прогноз)',
                    data: forecastEur,
                    borderColor: '#d32f2f',
                    borderDash: [5, 5],
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Прогноз курса валют' }
            }
        }
    });
}

// === Функции для вкладки Веры (преступность) ===

let crimeChart = null;
let crimeForecastChart = null;

async function loadCrime() {
    const windowSize = parseInt(document.getElementById('crimeWindowSize')?.value || 3);
    const forecastPeriods = parseInt(document.getElementById('crimeForecastPeriods')?.value || 3);

    const result = await sendToBackend(5001, {
        window_size: windowSize,
        forecast_periods: forecastPeriods
    });

    if (!result || result.status !== 'success') return;

    // Таблица
    let html = '<table><tr><th>Год</th><th>Убийства</th><th>Разбои</th><th>Кражи</th><th>Мошенничество</th><th>Наркотики</th><th>Экономические</th></tr>';
    result.table_data.forEach(row => {
        html += `<tr><td>${row.year}</td><td>${row.murder}</td><td>${row.robbery}</td><td>${row.theft}</td><td>${row.fraud}</td><td>${row.drugs}</td><td>${row.economic}</td></tr>`;
    });
    html += '</table>';
    document.getElementById('crimeTable').innerHTML = html;

    // Статистика
    document.getElementById('crimeStats').innerHTML = `
        <div class="stats-box">
            Максимальное снижение: <strong>${result.most_decreased.name} (${result.most_decreased.value}%)</strong><br>
            Минимальное снижение / рост: <strong>${result.most_increased.name} (${result.most_increased.value}%)</strong>
        </div>
    `;

    // Основной график
    const ctx = document.getElementById('crimeChart').getContext('2d');
    if (crimeChart) crimeChart.destroy();

    const colors = ['#e74c3c', '#e67e22', '#3498db', '#2ecc71', '#9b59b6', '#1abc9c'];
    const fields = result.fields;
    const datasets = fields.map((field, i) => ({
        label: field,
        data: result.values[field],
        borderColor: colors[i],
        tension: 0.3
    }));

    crimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: result.years,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Преступность в России' }
            }
        }
    });

    // График прогноза
    const forecastYears = result.forecast.map(f => f.year);
    const forecastDatasets = fields.map((field, i) => ({
        label: field + ' (прогноз)',
        data: result.forecast.map(f => f[field]),
        borderColor: colors[i],
        borderDash: [5, 5],
        tension: 0.3
    }));

    const ctxF = document.getElementById('crimeForecastChart').getContext('2d');
    if (crimeForecastChart) crimeForecastChart.destroy();

    crimeForecastChart = new Chart(ctxF, {
        type: 'line',
        data: {
            labels: forecastYears,
            datasets: forecastDatasets
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Прогноз преступности' }
            }
        }
    });
}