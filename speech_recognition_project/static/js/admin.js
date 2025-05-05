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
                        let type = 'total'; // Default to total users
                        if (index === 1) type = 'danger';
                        if (index === 2) type = 'risk';
                        
                        try {
                            const response = await fetch(`/get_users?type=${type}`);
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            const users = await response.json();
                            
                            userListContainer.innerHTML = `
                                <h3>${getUserTypeTitle(type)}列表</h3>
                                ${users.map(user => 
                                    `<div class="user-item" onclick="showUserDetails('${user.username}', '${type}')">${user.username}</div>`
                                ).join('')}
                            `;
                            userListContainer.style.display = 'block';
                            
                            // Hide user details panel
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


function showUserDetails(username, userType) {
    const userDetails = document.getElementById('userDetails');
    if (!userDetails) {
        console.error('用户详情容器未找到');
        return;
    }
    
    // 隐藏用户列表容器
    const userListContainer = document.querySelector('.user-list-container');
    if (userListContainer) {
        userListContainer.style.display = 'none';
    }
    
    // 显示用户详情面板并添加加载提示
    userDetails.style.display = 'block';
    userDetails.innerHTML = `
        <button class="back-button">←</button>
        <div class="user-detail-header">
            <h2 class="user-detail-title">用户 ${username} 的心理健康报告</h2>
        </div>
    `;
    
    // 发起请求获取用户详情
    fetch(`/get_user_details/${encodeURIComponent(username)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(userData => {
            let detailsHtml = `
                <button class="back-button">←</button>
                <div class="user-detail-header">
                    <h2 class="user-detail-title">用户 ${username} 的心理健康报告</h2>
                    <div class="user-status ${userData.status && userData.status.is_danger ? 'danger' : (userData.status && userData.status.is_risk ? 'risk' : 'normal')}">
                        <p class="status-text">当前状态: ${userData.status && userData.status.is_danger ? '需要立即干预' : (userData.status && userData.status.is_risk ? '需要关注' : '状态正常')}</p>
                        ${userData.status && userData.status.danger_level ? `<p class="danger-level">风险等级: ${userData.status.danger_level}</p>` : ''}
                    </div>
                </div>

                <div class="health-report-section">
                    <div class="symptoms-section">
                        <h3>📋 检测到的异常表现</h3>
                        <div class="symptoms-list">
            `;

            // 添加症状/行为记录
            if (userData.details && userData.details.danger_records && userData.details.danger_records.length > 0) {
                detailsHtml += userData.details.danger_records.map(record => `
                    <div class="symptom-item">
                        <div class="symptom-header">
                            <h4>${record.type}</h4>
                            <span class="symptom-time">检测时间: ${record.time}</span>
                        </div>
                        <p class="symptom-desc">${record.content}</p>
                        ${record.level ? `<p class="symptom-level">严重程度: ${record.level}</p>` : ''}
                    </div>
                `).join('');
            } else if (userData.details && userData.details.risk_records && userData.details.risk_records.length > 0) {
                detailsHtml += userData.details.risk_records.map(record => `
                    <div class="symptom-item">
                        <div class="symptom-header">
                            <h4>${record.type}</h4>
                            <span class="symptom-time">检测时间: ${record.time}</span>
                        </div>
                        <p class="symptom-desc">${record.content}</p>
                    </div>
                `).join('');
            } else {
                detailsHtml += '<p class="no-data">暂未检测到异常行为表现</p>';
            }

            detailsHtml += `
                        </div>
                    </div>

                    <div class="solutions-section">
                        <h3>💡 专业建议</h3>
                        <div class="solutions-list">
            `;

            // 添加解决方案
            if (userData.solutions && userData.solutions.length > 0) {
                detailsHtml += userData.solutions.map((solution, index) => `
                    <div class="solution-item">
                        <span class="solution-number">${index + 1}</span>
                        <p class="solution-content">${solution}</p>
                    </div>
                `).join('');
            } else {
                detailsHtml += '<p class="no-data">暂无具体建议</p>';
            }

            detailsHtml += `
                        </div>
                    </div>
                </div>
            `;

            userDetails.innerHTML = detailsHtml;

            // 重新添加返回按钮事件监听
            const backButton = userDetails.querySelector('.back-button');
            if (backButton) {
                backButton.addEventListener('click', function() {
                    userDetails.style.display = 'none';
                    if (userListContainer) {
                        userListContainer.style.display = 'block';
                    }
                });
            }
        })
        .catch(error => {
            console.error('获取用户详情失败:', error);
            userDetails.innerHTML = `
                <button class="back-button">←</button>
                <h2 class="user-detail-title">获取数据失败</h2>
                <div class="error-message">
                    <p>抱歉，获取用户详情时出现错误</p>
                    <p class="error-details">${error.message}</p>
                </div>
            `;
        });
}

// 修改点击事件处理函数
function handleBarClick(userType) {
    fetch(`/get_users?type=${userType}`)
        .then(response => response.json())
        .then(users => {
            const userList = document.getElementById('user-list');
            userList.innerHTML = `
                <h3>${getUserTypeTitle(userType)}列表</h3>
                <ul>
                    ${users.map(user => `
                        <li>
                            <a href="#" onclick="showUserDetails('${user.username}', '${userType}')">
                                ${user.username}
                            </a>
                        </li>
                    `).join('')}
                </ul>
            `;
        });
}

// 辅助函数：获取用户类型标题
function getUserTypeTitle(type) {
    switch(type) {
        case 'total':
            return '所有用户';
        case 'danger':
            return '危险用户';
        case 'risk':
            return '隐患用户';
        default:
            return '用户';
    }
}