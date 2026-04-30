let populationData = [];
let populationChart = null;
let forecastChart = null;

function loadPopulation() {
    const fileInput = document.getElementById('populationFile');
    const file = fileInput.files[0];
    if (!file) return alert('Выберите файл');

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            populationData = JSON.parse(e.target.result);
            showPopulationTable();
            showPopulationStats();
            drawPopulationChart();
        } catch (err) {
            alert('Ошибка чтения файла. Проверьте формат JSON.');
        }
    };
    reader.readAsText(file);
}

function showPopulationTable() {
    let html = '<table><tr><th>Год</th><th>Население (млн)</th><th>Изменение (%)</th></tr>';
    populationData.forEach((row, i) => {
        let change = '';
        if (i > 0) {
            const prev = populationData[i - 1].population;
            const diff = ((row.population - prev) / prev * 100).toFixed(2);
            const arrow = diff >= 0 ? '▲' : '▼';
            const color = diff >= 0 ? 'green' : 'red';
            change = `<span style="color:${color}">${arrow} ${diff}%</span>`;
        }
        html += `<tr><td>${row.year}</td><td>${row.population.toFixed(2)} млн</td><td>${change || '—'}</td></tr>`;
    });
    html += '</table>';
    document.getElementById('populationTable').innerHTML = html;
}

function showPopulationStats() {
    let maxGrowth = { value: -Infinity, year: '' };
    let maxDecline = { value: Infinity, year: '' };

    for (let i = 1; i < populationData.length; i++) {
        const prev = populationData[i - 1].population;
        const curr = populationData[i].population;
        const change = ((curr - prev) / prev) * 100;

        if (change > maxGrowth.value) {
            maxGrowth = { value: change, year: populationData[i].year };
        }
        if (change < maxDecline.value) {
            maxDecline = { value: change, year: populationData[i].year };
        }
    }

    document.getElementById('populationStats').innerHTML = `
        <div class="stats-box">
            Максимальный прирост: <strong>${maxGrowth.value.toFixed(2)}%</strong> в ${maxGrowth.year} году<br>
            Максимальная убыль: <strong>${maxDecline.value.toFixed(2)}%</strong> в ${maxDecline.year} году
        </div>
        <label>Окно скользящей средней: <input type="number" id="windowSize" value="3" min="2" max="10"></label>
        <label>Прогноз на лет: <input type="number" id="forecastPeriods" value="5" min="1" max="20"></label>
        <button onclick="calculateForecast()">Рассчитать прогноз</button>
    `;
}

function drawPopulationChart() {
    const ctx = document.getElementById('populationChart').getContext('2d');
    if (populationChart) populationChart.destroy();

    const years = populationData.map(d => d.year);
    const values = populationData.map(d => d.population);

    populationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Население (млн)',
                data: values,
                borderColor: '#1a237e',
                backgroundColor: 'rgba(26, 35, 126, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Численность населения России' }
            }
        }
    });
}

function calculateForecast() {
    const windowSize = parseInt(document.getElementById('windowSize').value);
    const periods = parseInt(document.getElementById('forecastPeriods').value);
    const values = populationData.map(d => d.population);
    const lastYear = populationData[populationData.length - 1].year;

    if (windowSize > values.length) {
        alert('Размер окна не может быть больше количества данных!');
        return;
    }

    // Скользящая средняя
    const forecastValues = [...values];
    for (let i = 0; i < periods; i++) {
        const slice = forecastValues.slice(forecastValues.length - windowSize);
        const avg = slice.reduce((a, b) => a + b, 0) / slice.length;
        forecastValues.push(avg);
    }

    // Будущие года
    const forecastYears = [];
    for (let i = 1; i <= periods; i++) {
        forecastYears.push(lastYear + i);
    }

    const forecastData = forecastValues.slice(values.length);

    // Отдельный график
    const ctx = document.getElementById('populationForecastChart').getContext('2d');
    if (forecastChart) forecastChart.destroy();

    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: forecastYears,
            datasets: [{
                label: 'Прогноз (скользящая средняя)',
                data: forecastData,
                borderColor: '#e53935',
                backgroundColor: 'rgba(229, 57, 53, 0.1)',
                fill: true,
                borderDash: [5, 5],
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Прогноз населения на будущие годы' }
            }
        }
    });

    document.getElementById('populationForecast').innerHTML = 
        `<div class="stats-box">Прогноз построен методом скользящей средней (окно: ${windowSize})</div>`;
}
