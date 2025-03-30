// 存储心情数据的结构
let moodHistory = [];

// 从localStorage加载数据
function loadMoodHistory() {
    const stored = localStorage.getItem('moodHistory');
    if (stored) {
        moodHistory = JSON.parse(stored);
        // 只保留最近5天的记录
        moodHistory = moodHistory.slice(-5);
    }
    updateHistoryList();
}

// 暴露给全局的添加心情函数
window.addMoodFromQA = function(text) {
    const now = new Date();
    const today = now.toLocaleDateString();
    const time = now.toLocaleTimeString();

    let todayRecord = moodHistory.find(day => day.date === today);
    if (!todayRecord) {
        todayRecord = {
            date: today,
            moods: []
        };
        moodHistory.push(todayRecord);
    }

    todayRecord.moods.push({
        time: time,
        text: text
    });

    // 只保留最近5天的记录
    if (moodHistory.length > 5) {
        moodHistory.shift();
    }

    // 保存到localStorage
    localStorage.setItem('moodHistory', JSON.stringify(moodHistory));
    
    // 如果在日记页面，更新显示
    if (document.querySelector('.mood-flow')) {
        updateHistoryList();
        showDayMood(moodHistory.length - 1);
    }
    
    console.log('心情已添加:', text); // 调试信息
};

// 保存数据到localStorage
function saveMoodHistory() {
    localStorage.setItem('moodHistory', JSON.stringify(moodHistory));
}

// 修改更新历史记录列表函数
function updateHistoryList() {
    const historyList = document.querySelector('.history-list');
    historyList.innerHTML = '';
    
    moodHistory.forEach((day, index) => {
        const li = document.createElement('li');
        li.className = 'history-item';
        li.innerHTML = `
            <div class="history-header">
                <div class="history-date">${day.date}</div>
                <button class="delete-day" title="删除这一天的记录">×</button>
            </div>
            <div class="history-content">
                ${day.moods.map((mood) => `
                    <div class="history-mood-item">
                        <span class="mood-time">${mood.time}</span>
                        <span class="mood-text">${mood.text}</span>
                    </div>
                `).join('')}
            </div>
        `;
        
        // 为删除按钮添加事件监听器
        li.querySelector('.delete-day').addEventListener('click', (e) => {
            e.stopPropagation(); // 阻止事件冒泡
            // 删除这一天的记录
            moodHistory.splice(index, 1);
            
            // 保存并更新显示
            saveMoodHistory();
            updateHistoryList();
            
            // 如果还有记录，显示最新的一天
            if (moodHistory.length > 0) {
                showDayMood(moodHistory.length - 1);
            } else {
                document.querySelector('.mood-flow').innerHTML = '';
            }
        });
        
        li.onclick = () => showDayMood(index);
        historyList.appendChild(li);
    });
}

// 修改显示某一天的心情记录函数
function showDayMood(index) {
    const moodFlow = document.querySelector('.mood-flow');
    const day = moodHistory[index];
    const todayTitle = document.querySelector('.diary-page .page-title');
    
    // 更新左侧标题
    if (todayTitle) {
        const today = new Date().toLocaleDateString();
        if (day.date === today) {
            todayTitle.textContent = '今日心情';
        } else {
            todayTitle.textContent = `${day.date} 心情`;
        }
    }
    
    moodFlow.innerHTML = '';
    day.moods.forEach(mood => {
        const div = document.createElement('div');
        div.className = 'mood-item';
        div.innerHTML = `
            <span class="mood-time">${mood.time}</span>
            <span class="mood-text">${mood.text}</span>
        `;
        moodFlow.appendChild(div);
    });

    // 更新选中状态
    document.querySelectorAll('.history-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });
}

// 添加新的心情记录
function addMood(text) {
    const now = new Date();
    const today = now.toLocaleDateString();
    const time = now.toLocaleTimeString();

    let todayRecord = moodHistory.find(day => day.date === today);
    if (!todayRecord) {
        todayRecord = {
            date: today,
            moods: []
        };
        moodHistory.push(todayRecord);
    }

    todayRecord.moods.push({
        time: time,
        text: text
    });

    // 只保留最近5天的记录
    if (moodHistory.length > 5) {
        moodHistory.shift();
    }

    saveMoodHistory();
    updateHistoryList();
    showDayMood(moodHistory.length - 1);
}

// 初始化
// 确保在DOM加载完成后再执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化函数
    function loadMoodHistory() {
        const stored = localStorage.getItem('moodHistory');
        const chatList = document.querySelector('.history-list');
        
        // 如果不在日记页面，直接返回
        if (!chatList) return;
        
        if (stored) {
            moodHistory = JSON.parse(stored);
            moodHistory = moodHistory.slice(-5);
        }
        updateHistoryList();
    }

    // 如果有今天的记录，显示今天的记录
    if (moodHistory.length > 0) {
        showDayMood(moodHistory.length - 1);
    }
    // 只在日记页面才初始化
    if (document.querySelector('.diary-container')) {
        loadMoodHistory();
    }
});