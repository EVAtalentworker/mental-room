document.addEventListener('DOMContentLoaded', function() {
    let userListContainer = null;
    const userDetails = document.getElementById('userDetails');

    // 将 handleUserClick 定义为全局函数
    window.handleUserClick = async function(username) {
        try {
            const response = await fetch(`/get_user_details/${username}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const userData = await response.json();
            
            // 隐藏用户列表
            if (userListContainer) {
                userListContainer.style.display = 'none';
            }
            
            // 显示用户详情
            const userDetails = document.getElementById('userDetails');
            userDetails.querySelector('.user-detail-title').textContent = `用户: ${username}`;
            
            // 显示症状
            const symptomsList = userDetails.querySelector('.symptoms-list');
            symptomsList.innerHTML = userData.symptoms.length > 0 
                ? userData.symptoms.map(symptom => 
                    `<div class="symptom-item">${symptom.name} (频率: ${symptom.frequency})</div>`
                ).join('')
                : '<div class="symptom-item">暂无检测到的症状</div>';
            
            // 显示解决方案
            const solutionsList = userDetails.querySelector('.solutions-list');
            solutionsList.innerHTML = userData.solutions.length > 0
                ? userData.solutions.map(solution =>
                    `<div class="solution-item">${solution}</div>`
                ).join('')
                : '<div class="solution-item">暂无相关解决方案</div>';
            
            userDetails.style.display = 'block';
        } catch (error) {
            console.error('获取用户详情失败:', error);
        }
    };

    function createUserList() {
        const container = document.createElement('div');
        container.className = 'user-list-container';
        document.querySelector('.upper-section').appendChild(container);
        return container;
    }

    async function updateChart() {
        const ctx = document.getElementById('userStatsChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['总用户', '危险用户', '隐患用户'],
                datasets: [{
                    data: [totalUsers, dangerUsers, riskUsers],
                    backgroundColor: [
                        '#4CAF50',
                        '#f44336',
                        '#FFD700'
                    ]
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
                        let type = 'all';
                        if (index === 1) type = 'danger';
                        if (index === 2) type = 'risk';
                        
                        try {
                            const response = await fetch(`/get_users?type=${type}`);
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            const users = await response.json();
                            
                            userListContainer.innerHTML = `
                                <h3>${index === 0 ? '所有用户' : index === 1 ? '危险用户' : '隐患用户'}</h3>
                                ${users.map(user => 
                                    `<div class="user-item" onclick="handleUserClick('${user.username}')">${user.username}</div>`
                                ).join('')}
                            `;
                            userListContainer.style.display = 'block';
                            
                            // 隐藏用户详情面板
                            const userDetails = document.getElementById('userDetails');
                            if (userDetails) {
                                userDetails.style.display = 'none';
                            }
                        } catch (error) {
                            console.error('获取用户列表失败:', error);
                        }
                    }
                }
            }
        });
    }

    // 添加返回按钮事件监听
    const backButton = document.querySelector('.back-button');
    if (backButton) {
        backButton.addEventListener('click', function() {
            const userDetails = document.getElementById('userDetails');
            if (userDetails) {
                userDetails.style.display = 'none';
            }
            if (userListContainer) {
                userListContainer.style.display = 'block';
            }
        });
    }

    // 初始化图表
    updateChart();
});