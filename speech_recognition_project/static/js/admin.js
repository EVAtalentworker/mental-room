document.addEventListener('DOMContentLoaded', function() {
    let userListContainer = null;

    function createUserList() {
        const container = document.createElement('div');
        container.className = 'user-list-container';
        document.querySelector('.upper-section').appendChild(container);
        return container;
    }

    const ctx = document.getElementById('userStatsChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['已注册账户', '危险账户'],
            datasets: [{
                data: [totalUsers, dangerUsers],
                backgroundColor: [
                    'rgba(200, 200, 200, 0.8)',
                    'rgba(255, 99, 132, 0.8)'
                ],
                borderColor: [
                    'rgba(200, 200, 200, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: Math.max(totalUsers, dangerUsers) + 1,
                    ticks: {
                        stepSize: 1,
                        precision: 0,
                        color: '#333',
                        font: {
                            size: 14
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#333',
                        font: {
                            size: 14
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            onClick: async function(event, elements) {
                if (elements && elements.length > 0) {
                    if (!userListContainer) {
                        userListContainer = createUserList();
                    }
                    
                    const element = elements[0];
                    const index = element.index;
                    
                    try {
                        const response = await fetch(`/get_users?type=${index === 0 ? 'all' : 'danger'}`);
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        const data = await response.json();
                        
                        const users = data;
                        if (users && users.length > 0) {
                            userListContainer.innerHTML = `
                                <h3>${index === 0 ? '所有用户' : '危险用户'}</h3>
                                ${users.map(user => 
                                    `<div class="user-item">${user.username}</div>`
                                ).join('')}
                            `;
                            userListContainer.style.display = 'block';
                        } else {
                            userListContainer.innerHTML = `
                                <h3>${index === 0 ? '所有用户' : '危险用户'}</h3>
                                <div class="user-item">暂无用户数据</div>
                            `;
                            userListContainer.style.display = 'block';
                        }
                    } catch (error) {
                        console.error('请求失败:', error);
                        userListContainer.innerHTML = `
                            <h3>获取用户数据失败</h3>
                            <div class="user-item">请稍后重试</div>
                        `;
                        userListContainer.style.display = 'block';
                    }
                }
            }
        }
    });

    // 点击其他地方关闭用户列表
    document.addEventListener('click', function(event) {
        if (userListContainer && !event.target.closest('.user-list-container') && !event.target.closest('canvas')) {
            userListContainer.remove();
            userListContainer = null;
        }
    });
});