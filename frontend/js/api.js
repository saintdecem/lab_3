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

// ========== ВКЛАДКА ЛИЗЫ (ВАЛЮТА) ==========

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

    // Основной график — как у Лизы: USD синий, EUR красный
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
                    borderColor: '#1f77b4',    // синий (как matplotlib 'b')
                    backgroundColor: 'rgba(31, 119, 180, 0.1)',
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: '#1f77b4',
                    tension: 0.3
                },
                {
                    label: 'EUR/RUB',
                    data: result.eur_values,
                    borderColor: '#d62728',    // красный (как matplotlib 'r')
                    backgroundColor: 'rgba(214, 39, 40, 0.1)',
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: '#d62728',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Курс рубля к USD и EUR' },
                legend: { labels: { usePointStyle: true } }
            },
            scales: {
                x: { grid: { display: false } },
                y: { 
                    grid: { color: 'rgba(0, 0, 0, 0.1)' },
                    title: { display: true, text: 'Курс (руб.)' }
                }
            }
        }
    });

    // График прогноза — как у Лизы: USD циан, EUR магента
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
                    borderColor: '#17becf',    // циан (как matplotlib 'c')
                    backgroundColor: 'rgba(23, 190, 207, 0.1)',
                    fill: true,
                    borderDash: [5, 5],
                    pointStyle: 'rectRounded',
                    pointRadius: 4,
                    tension: 0.3
                },
                {
                    label: 'EUR (прогноз)',
                    data: forecastEur,
                    borderColor: '#e377c2',    // магента (как matplotlib 'm')
                    backgroundColor: 'rgba(227, 119, 194, 0.1)',
                    fill: true,
                    borderDash: [5, 5],
                    pointStyle: 'rectRounded',
                    pointRadius: 4,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Прогноз курса валют' },
                legend: { labels: { usePointStyle: true } }
            },
            scales: {
                x: { grid: { display: false } },
                y: { 
                    grid: { color: 'rgba(0, 0, 0, 0.1)' },
                    title: { display: true, text: 'Курс (руб.)' }
                }
            }
        }
    });
}

// ========== ВКЛАДКА ВЕРЫ (ПРЕСТУПНОСТЬ) ==========

let crimeChart = null;
let crimeForecastChart = null;

// Цвета как у Веры в PyQt5
const VERA_COLORS = {
    'murder':   '#e74c3c',
    'robbery':  '#e67e22',
    'theft':    '#3498db',
    'fraud':    '#2ecc71',
    'drugs':    '#9b59b6',
    'economic': '#1abc9c'
};

const VERA_LABELS = {
    'murder':   'Murder',
    'robbery':  'Robbery',
    'theft':    'Theft',
    'fraud':    'Fraud',
    'drugs':    'Drugs',
    'economic': 'Economic'
};

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

    // Основной график — как у Веры
    const ctx = document.getElementById('crimeChart').getContext('2d');
    if (crimeChart) crimeChart.destroy();

    const fields = result.fields;
    const datasets = fields.map(field => ({
        label: VERA_LABELS[field] || field,
        data: result.values[field],
        borderColor: VERA_COLORS[field] || '#000',
        backgroundColor: 'transparent',
        pointRadius: 4,
        pointBackgroundColor: VERA_COLORS[field] || '#000',
        borderWidth: 2,
        tension: 0
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
                title: { display: true, text: 'Преступность в России' },
                legend: { 
                    labels: { usePointStyle: true },
                    position: 'top'
                }
            },
            scales: {
                x: { 
                    grid: { color: 'rgba(0, 0, 0, 0.06)' },
                    title: { display: true, text: 'Год' }
                },
                y: { 
                    grid: { color: 'rgba(0, 0, 0, 0.06)' },
                    title: { display: true, text: 'Количество (тыс.)' }
                }
            }
        }
    });

    // График прогноза — как у Веры: пунктирные линии
    const forecastYears = result.forecast.map(f => f.year);
    const forecastDatasets = fields.map(field => ({
        label: (VERA_LABELS[field] || field) + ' (прогноз)',
        data: result.forecast.map(f => f[field]),
        borderColor: VERA_COLORS[field] || '#000',
        backgroundColor: 'transparent',
        borderDash: [8, 4],
        borderWidth: 2,
        pointRadius: 0,
        tension: 0
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
                title: { display: true, text: 'Прогноз преступности' },
                legend: { 
                    labels: { usePointStyle: true },
                    position: 'top'
                }
            },
            scales: {
                x: { 
                    grid: { color: 'rgba(0, 0, 0, 0.06)' },
                    title: { display: true, text: 'Год' }
                },
                y: { 
                    grid: { color: 'rgba(0, 0, 0, 0.06)' },
                    title: { display: true, text: 'Количество (тыс.)' }
                }
            }
        }
    });
}