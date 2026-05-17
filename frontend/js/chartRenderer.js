class ChartRenderer {
    constructor() {
        this.charts = {};
    }

    drawLineChart(canvasId, labels, datasets, title, fill = true) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        const chartDatasets = datasets.map(ds => ({
            label: ds.label,
            data: ds.data,
            borderColor: ds.color,
            backgroundColor: ds.color.replace(')', ', 0.1)').replace('rgb', 'rgba'),
            fill: fill,
            borderDash: ds.dashed ? [5, 5] : [],
            tension: 0.3
        }));

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: chartDatasets
            },
            options: {
                responsive: true,
                plugins: {
                    title: { display: true, text: title }
                }
            }
        });

        return this.charts[canvasId];
    }

    exportAsPNG(canvasId, name) {
        const canvas = document.getElementById(canvasId);
        const link = document.createElement('a');
        link.download = `график_${name}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }
}