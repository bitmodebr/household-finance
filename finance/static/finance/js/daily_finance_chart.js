const financeChartCanvas = document.getElementById('dailyFinanceChart');

if (financeChartCanvas) {
    const financeChartData = JSON.parse(
        document.getElementById('daily-finance-chart-data').textContent,
    );
    const currencyFormatter = new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    });

    new Chart(financeChartCanvas, {
        type: 'bar',
        data: financeChartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label(context) {
                            return `${context.dataset.label}: ${currencyFormatter.format(context.parsed.y)}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Dia do mês',
                    },
                },
                y: {
                    beginAtZero: true,
                    grace: '5%',
                    title: {
                        display: true,
                        text: 'Valor (R$)',
                    },
                    ticks: {
                        callback(value) {
                            return currencyFormatter.format(value);
                        },
                    },
                },
            },
        },
    });
}
