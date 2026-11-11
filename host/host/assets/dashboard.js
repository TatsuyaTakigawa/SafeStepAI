(() => {
    const status = document.getElementById('chart-status');
    const hourlyCanvas = document.getElementById('hourly-chart');
    const directionCanvas = document.getElementById('direction-chart');

    if (!status || !hourlyCanvas || !directionCanvas) {
        return;
    }

    if (typeof Chart === 'undefined') {
        status.textContent = 'グラフライブラリを読み込めませんでした。';
        return;
    }

    fetch('api/analytics.php', { headers: { Accept: 'application/json' } })
        .then((response) => {
            if (!response.ok) {
                throw new Error('Analytics request failed');
            }
            return response.json();
        })
        .then((data) => {
            const hours = Array.isArray(data.hours) ? data.hours : [];
            if (hours.length === 0) {
                status.textContent = '直近24時間のイベントデータはありません。';
                return;
            }

            status.hidden = true;
            new Chart(hourlyCanvas, {
                data: {
                    labels: hours.map((row) => row.hour.slice(5)),
                    datasets: [
                        {
                            type: 'bar',
                            label: '推定人数',
                            data: hours.map((row) => Number(row.people_count)),
                            backgroundColor: '#087e78',
                            borderRadius: 3,
                            yAxisID: 'people',
                        },
                        {
                            type: 'line',
                            label: '逆走率',
                            data: hours.map((row) => Number(row.total) > 0
                                ? Number(row.reverse_count) / Number(row.total) * 100
                                : 0),
                            borderColor: '#b43d35',
                            backgroundColor: '#b43d35',
                            pointRadius: 3,
                            tension: 0.25,
                            yAxisID: 'rate',
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { position: 'top' } },
                    scales: {
                        people: {
                            beginAtZero: true,
                            title: { display: true, text: '推定人数' },
                            ticks: { precision: 0 },
                        },
                        rate: {
                            beginAtZero: true,
                            max: 100,
                            position: 'right',
                            title: { display: true, text: '逆走率' },
                            ticks: { callback: (value) => `${value}%` },
                            grid: { drawOnChartArea: false },
                        },
                    },
                },
            });

            const totalEvents = hours.reduce((sum, row) => sum + Number(row.total), 0);
            const reverseEvents = hours.reduce((sum, row) => sum + Number(row.reverse_count), 0);
            new Chart(directionCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['通常', '逆走'],
                    datasets: [{
                        data: [totalEvents - reverseEvents, reverseEvents],
                        backgroundColor: ['#087e78', '#b43d35'],
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '66%',
                    plugins: { legend: { position: 'bottom' } },
                },
            });
        })
        .catch(() => {
            status.hidden = false;
            status.textContent = 'グラフデータを取得できませんでした。';
        });
})();