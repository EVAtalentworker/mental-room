document.addEventListener('DOMContentLoaded', function() {
    let chart = null;

    function updateStatusInfo(data) {
        const negativeCount = Object.values(data.dangerous_words).reduce((a, b) => a + b, 0);
        const daysUsed = data.days_used || 1;
        const dailyAverage = (negativeCount / daysUsed).toFixed(2);
        
        const dailyNegativeContainer = document.getElementById('dailyNegativeContainer');
        const dailyNegativeElement = document.getElementById('dailyNegative');
        const userStatusElement = document.getElementById('userStatus');
        const statusMessageElement = document.getElementById('statusMessage');
        
        // 移除所有状态类
        userStatusElement.classList.remove('status-excellent', 'status-good', 'status-moderate', 'status-negative');
        
        if (negativeCount === 0) {
            // 没有消极词时的默认状态
            dailyNegativeContainer.style.display = 'none';
            userStatusElement.textContent = '良好';
            userStatusElement.classList.add('status-good');
            statusMessageElement.textContent = '状态不错，其实你只需要登录几天并且不说话，就能到积极了';
        } else {
            // 有消极词时显示具体数据
            dailyNegativeContainer.style.display = 'block';
            dailyNegativeElement.textContent = dailyAverage;
            
            if (dailyAverage < 1) {
                userStatusElement.textContent = '优秀';
                userStatusElement.classList.add('status-excellent');
                statusMessageElement.textContent = '你是一个积极的人，我诚信祝愿你能如此快乐地活下去';
            } else if (dailyAverage < 2) {
                userStatusElement.textContent = '良好';
                userStatusElement.classList.add('status-good');
                statusMessageElement.textContent = '状态不错，其实你只需要登录几天并且不说话，就能到积极了';
            } else if (dailyAverage < 3) {
                userStatusElement.textContent = '适中';
                userStatusElement.classList.add('status-moderate');
                statusMessageElement.textContent = '再这样下去要变消极了';
            } else {
                userStatusElement.textContent = '消极';
                userStatusElement.classList.add('status-negative');
                statusMessageElement.textContent = '过完一个悲惨的人生';
            }
        }
    }

    function updateChart() {
        fetch('/get_mood_statistics')
            .then(response => response.json())
            .then(data => {
                const ctx = document.getElementById('dangerWordsChart').getContext('2d');
                
                // 更新状态信息
                updateStatusInfo(data);
                
                if (chart) {
                    chart.destroy();
                }
                
                // 统计消极词总数
                const negativeCount = Object.values(data.dangerous_words).reduce((a, b) => a + b, 0);
                
                const stats = {
                    'POSITIVE': data.positive_sentences.length,
                    'NEGATIVE': negativeCount  // 直接使用消极词总数
                };
                
                chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(stats),
                        datasets: [{
                            label: '出现次数',
                            data: Object.values(stats),
                            backgroundColor: [
                                'rgba(75, 192, 192, 0.8)',
                                'rgba(255, 99, 132, 0.8)'
                            ],
                            borderColor: [
                                'rgba(75, 192, 192, 1)',
                                'rgba(255, 99, 132, 1)'
                            ],
                            borderWidth: 1,
                            barThickness: 30,
                            maxBarThickness: 35
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `数量: ${context.raw}`;
                                    }
                                }
                            },  // 添加逗号
                            title: {
                                display: true,
                                text: '语言情感分析统计',
                                font: {
                                    size: 16
                                }
                            },
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error:', error));
    }

    // 初始加载
    updateChart();

    // 每30秒更新一次
    setInterval(updateChart, 30000);
});