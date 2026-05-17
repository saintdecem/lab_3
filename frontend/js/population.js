class PopulationApp {
    constructor() {
        this.data = [];
        this.chartRenderer = new ChartRenderer();
        this.populationChart = null;
        this.forecastChart = null;
    }

    loadFromFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                this.data = JSON.parse(e.target.result);
                this.data.sort((a, b) => a.year - b.year);
                this.showTable();
                this.showStats();
                this.drawChart();
            } catch (err) {
                alert('Ошибка чтения файла. Проверьте формат JSON.');
            }
        };
        reader.readAsText(file);
    }

    showTable() {
        let html = '<table><tr><th>Год</th><th>Население (млн)</th><th>Изменение (%)</th></tr>';
        this.data.forEach((row, i) => {
            let change = '';
            if (i > 0) {
                const prev = this.data[i - 1].population;
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

    showStats() {
        let maxGrowth = { value: -Infinity, year: '', absolute: 0 };
        let maxDecline = { value: Infinity, year: '', absolute: 0 };

        for (let i = 1; i < this.data.length; i++) {
            const prev = this.data[i - 1].population;
            const curr = this.data[i].population;
            const change = ((curr - prev) / prev) * 100;
            const absolute = curr - prev;

            if (change > maxGrowth.value) {
                maxGrowth = { value: change, year: this.data[i].year, absolute: absolute };
            }
            if (change < maxDecline.value) {
                maxDecline = { value: change, year: this.data[i].year, absolute: absolute };
            }
        }

        document.getElementById('populationStats').innerHTML = `
            <div class="stats-box">
                Максимальный прирост: <strong>${maxGrowth.value.toFixed(2)}% (${maxGrowth.absolute > 0 ? '+' : ''}${maxGrowth.absolute.toFixed(2)} млн)</strong> в ${maxGrowth.year} году<br>
                Максимальная убыль: <strong>${maxDecline.value.toFixed(2)}% (${maxDecline.absolute.toFixed(2)} млн)</strong> в ${maxDecline.year} году
            </div>
            <label>Окно скользящей средней: <input type="number" id="windowSize" value="3" min="2" max="10"></label>
            <label>Прогноз на лет: <input type="number" id="forecastPeriods" value="5" min="1" max="20"></label>
            <button onclick="app.calculateForecast()">Рассчитать прогноз</button>
        `;
    }

    drawChart() {
        const years = this.data.map(d => d.year);
        const values = this.data.map(d => d.population);
        this.populationChart = this.chartRenderer.drawLineChart(
            'populationChart',
            years,
            [{ label: 'Население (млн)', data: values, color: '#1a237e' }],
            'Численность населения России'
        );
    }

    calculateForecast() {
        if (this.data.length === 0) {
            alert('Сначала загрузите данные!');
            return;
        }

        const windowSize = parseInt(document.getElementById('windowSize').value);
        const periods = parseInt(document.getElementById('forecastPeriods').value);
        const values = this.data.map(d => d.population);
        const lastYear = this.data[this.data.length - 1].year;

        if (windowSize > values.length) {
            alert('Размер окна не может быть больше количества данных!');
            return;
        }

        const forecastValues = [...values];
        for (let i = 0; i < periods; i++) {
            const slice = forecastValues.slice(forecastValues.length - windowSize);
            const avg = slice.reduce((a, b) => a + b, 0) / slice.length;
            forecastValues.push(avg);
        }

        const forecastYears = [];
        for (let i = 1; i <= periods; i++) {
            forecastYears.push(lastYear + i);
        }

        const forecastData = forecastValues.slice(values.length);

        this.forecastChart = this.chartRenderer.drawLineChart(
            'populationForecastChart',
            forecastYears,
            [{ label: 'Прогноз (скользящая средняя)', data: forecastData, color: '#e53935', dashed: true }],
            'Прогноз населения на будущие годы'
        );

        document.getElementById('populationForecast').innerHTML = 
            `<div class="stats-box">Прогноз построен методом скользящей средней (окно: ${windowSize})</div>`;
    }

    exportChart(canvasId, name) {
        this.chartRenderer.exportAsPNG(canvasId, name);
    }
}

// Единственная глобальная переменная — экземпляр приложения
const app = new PopulationApp();

// Короткие функции для вызова из HTML (по кнопкам)
function loadPopulation() {
    const fileInput = document.getElementById('populationFile');
    const file = fileInput.files[0];
    if (!file) return alert('Выберите файл');
    app.loadFromFile(file);
}

function calculateForecast() {
    app.calculateForecast();
}

function exportChart(canvasId, name) {
    app.exportChart(canvasId, name);
}