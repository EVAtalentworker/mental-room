let diaries = JSON.parse(localStorage.getItem('diaries') || '[]');
let currentDiaryId = null;

// 修改初始化部分
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    const editorContent = document.querySelector('.editor-content');
    const addBtn = document.getElementById('add-diary-btn');
    
    if (diaries.length > 0) {
        currentDiaryId = diaries[0].id;
        loadDiaryToEditor(diaries[0]);
        editorContent.classList.remove('disabled');
        addBtn.classList.remove('glowing');
    } else {
        editorContent.classList.add('disabled');
        addBtn.classList.add('glowing');
        editorContent.setAttribute('contenteditable', 'false');
        editorContent.innerHTML = '';
    }
});

// 添加一个辅助函数来检查是否已存在今天的日记
// 修改检查今日日记的函数
function hasTodayDiary() {
    const today = new Date();
    const todayStr = today.toLocaleDateString();
    return diaries.some(diary => diary.date === todayStr);
}

// 添加一个检查特定日期日记的函数
function hasDiaryForDate(dateStr) {
    return diaries.some(diary => diary.title === dateStr);
}

// 修改 setupEventListeners 中的 addBtn 事件监听部分
function setupEventListeners() {
    const editorContent = document.querySelector('.editor-content');
    const popupBtn = document.getElementById('diary-popup-btn');
    const addBtn = document.getElementById('add-diary-btn');
    const popup = document.getElementById('diary-popup');
    
    if (editorContent) {
        editorContent.addEventListener('input', handleEditorChange);
    }
    
    if (addBtn) {
        addBtn.addEventListener('click', () => {
            const today = new Date();
            const todayStr = today.toLocaleDateString();
            
            if (hasTodayDiary()) {
                // 创建可编辑的新日记模板
                createCustomDateDiary();
            } else {
                createNewDiary(); // 直接创建今天的日记
            }
        });
    }
    
    if (popupBtn && popup) {
        popupBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            popup.classList.toggle('show');
            if (popup.classList.contains('show')) {
                loadPopupDiaries();
            }
        });
        
        // 点击其他地方关闭弹窗
        document.addEventListener('click', (e) => {
            if (!popup.contains(e.target) && !popupBtn.contains(e.target)) {
                popup.classList.remove('show');
            }
        });
    }
    
    window.addEventListener('blur', autoSaveDiary);
    window.addEventListener('beforeunload', autoSaveDiary);
}

// 删除 loadDiaries 函数中的 DOM 操作部分，只保留存储功能
function loadDiaries() {
    saveDiariesToStorage();
}

function loadPopupDiaries() {
    const popup = document.getElementById('diary-popup');
    if (!popup) return;
    
    popup.innerHTML = '';
    
    if (diaries.length === 0) {
        popup.innerHTML = '<div class="popup-empty">暂无日记</div>';
        return;
    }
    
    diaries.forEach(diary => {
        const item = document.createElement('div');
        item.className = 'diary-item';
        item.dataset.id = diary.id;  // 添加 data-id 属性
        if (diary.id === currentDiaryId) {
            item.classList.add('active');
        }
        
        // 创建日记内容容器
        const contentContainer = document.createElement('div');
        contentContainer.className = 'diary-content-container';
        contentContainer.innerHTML = `
            <div class="diary-title">${diary.title}</div>
            <div class="diary-time">${diary.date} ${diary.time}</div>
        `;
        
        // 创建删除按钮
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();  // 阻止事件冒泡
            deleteDiary(diary.id);
        };
        
        // 组装元素
        item.appendChild(contentContainer);
        item.appendChild(deleteBtn);
        
        // 点击日记切换显示
        contentContainer.addEventListener('click', () => {
            currentDiaryId = diary.id;
            loadDiaryToEditor(diary);
            updateActiveState();
            popup.classList.remove('show');
        });
        
        popup.appendChild(item);
    });
}

function addNewDiarySection() {
    if (hasTodayDiary()) {
        alert('已有今日的日记');
        return;
    }

    const editorContent = document.querySelector('.editor-content');
    if (!editorContent) return;
    
    // 创建新的日记部分
    const date = new Date();
    const formattedDate = `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
    
    const newSection = document.createElement('div');
    newSection.className = 'diary-section';
    newSection.innerHTML = `<div>${formattedDate}</div><div><br></div>`;
    
    // 添加到编辑器
    editorContent.appendChild(newSection);
    
    // 滚动到新部分
    setTimeout(() => {
        newSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    // 自动保存
    autoSaveDiary();
}

function createNewDiary() {
    const editorContent = document.querySelector('.editor-content');
    const addBtn = document.getElementById('add-diary-btn');
    
    const date = new Date();
    const formattedDate = `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
    
    const newDiary = {
        id: Date.now(),
        title: formattedDate,
        content: `<div class="diary-section"><div>${formattedDate}</div><div><br></div></div>`,
        date: date.toLocaleDateString(),
        time: date.toLocaleTimeString()
    };
    
    diaries.unshift(newDiary);
    currentDiaryId = newDiary.id;
    
    editorContent.classList.remove('disabled');
    editorContent.setAttribute('contenteditable', 'true');
    addBtn.classList.remove('glowing');
    
    saveDiariesToStorage();
    loadDiaryToEditor(newDiary);
    loadPopupDiaries();
}

function handleEditorChange() {
    const editorContent = document.querySelector('.editor-content');
    if (!editorContent) return;

    // 确保每个部分都有标题行
    const sections = editorContent.querySelectorAll('.diary-section');
    sections.forEach(section => {
        if (!section.firstElementChild) {
            section.innerHTML = '<div>新日记</div><div><br></div>';
        }
    });
    
    autoSaveDiary();
}

function autoSaveDiary() {
    if (!currentDiaryId) return;
    
    const editorContent = document.querySelector('.editor-content');
    if (!editorContent) return;
    
    const content = editorContent.innerHTML;
    const diaryIndex = diaries.findIndex(d => d.id === currentDiaryId);
    if (diaryIndex !== -1) {
        // 只保存内容，不更新标题
        diaries[diaryIndex].content = content;
        saveDiariesToStorage();
    }
}

function loadDiaryToEditor(diary) {
    const editorContent = document.querySelector('.editor-content');
    if (!editorContent) return;
    
    // 清空现有内容
    editorContent.innerHTML = '';
    
    // 将日记内容解析为 DOM 元素
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = diary.content;
    
    // 确保内容有正确的 diary-section 结构
    if (!tempDiv.querySelector('.diary-section')) {
        const section = document.createElement('div');
        section.className = 'diary-section';
        section.innerHTML = tempDiv.innerHTML;
        editorContent.appendChild(section);
    } else {
        editorContent.innerHTML = diary.content;
        // 设置所有日记部分的标题为不可编辑
        editorContent.querySelectorAll('.diary-section > div:first-child').forEach(titleDiv => {
            titleDiv.contentEditable = false;
        });
    }
}

function addNewDiarySection() {
    const editorContent = document.querySelector('.editor-content');
    if (!editorContent) return;
    
    // 创建新的日记部分
    const date = new Date();
    const formattedDate = `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
    
    const newSection = document.createElement('div');
    newSection.className = 'diary-section';
    newSection.innerHTML = `<div>${formattedDate}</div><div><br></div>`;
    
    // 添加到编辑器
    editorContent.appendChild(newSection);
    
    // 滚动到新部分
    setTimeout(() => {
        newSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    // 自动保存
    autoSaveDiary();
}

// 删除重复的 loadDiaryToEditor 函数
// 删除不需要的 saveDiary 函数

function updateActiveState() {
    document.querySelectorAll('.diary-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.id === currentDiaryId) {
            item.classList.add('active');
        }
    });
}

function saveDiariesToStorage() {
    localStorage.setItem('diaries', JSON.stringify(diaries));
}

// 添加新函数：创建自定义日期的日记
// 在 createCustomDateDiary 函数中修改成功创建日记的部分
function createCustomDateDiary() {
    const editorContent = document.querySelector('.editor-content');
    
    // 创建临时日记部分
    const tempSection = document.createElement('div');
    tempSection.className = 'diary-section temp-section';
    tempSection.innerHTML = `
        <div contenteditable="true" class="date-input" placeholder="请输入日期">YYYY.MM.DD</div>
        <div><br></div>
    `;
    
    // 添加到现有内容下方
    editorContent.appendChild(tempSection);
    
    // 滚动到新部分
    setTimeout(() => {
        tempSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    // 添加日期输入事件监听
    const dateInput = tempSection.querySelector('.date-input');
    if (dateInput) {
        // 添加键盘事件监听器
        dateInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                tempSection.remove();
            }
        });

        // 添加输入事件监听器，用于跟踪是否有修改
        let hasChanged = false;
        dateInput.addEventListener('input', function() {
            const currentText = this.textContent.trim();
            hasChanged = currentText !== 'YYYY.MM.DD';
        });

        // 修改失焦事件处理
        dateInput.addEventListener('blur', function() {
            const inputDate = this.textContent.trim();
            
            // 检查是否包含特殊字符或占位符
            if (inputDate.includes('Y') || inputDate.includes('M') || inputDate.includes('D') || /[^0-9.]/.test(inputDate)) {
                tempSection.remove();
                return;
            }
            
            // 其他验证保持不变
            const datePattern = /^\d{4}\.\d{2}\.\d{2}$/;
            
            if (!datePattern.test(inputDate)) {
                alert('请按格式输入日期：YYYY.MM.DD');
                tempSection.remove();
                return;
            }
            
            if (hasDiaryForDate(inputDate)) {
                alert('已有此日日记');
                tempSection.remove();
                return;
            }
            
            // 创建新日记
            const finalDiary = {
                id: Date.now(),
                title: inputDate,
                content: `<div class="diary-section"><div>${inputDate}</div><div><br></div></div>`,
                date: new Date().toLocaleDateString(),
                time: new Date().toLocaleTimeString()
            };
            
            diaries.unshift(finalDiary);
            currentDiaryId = finalDiary.id;
            saveDiariesToStorage();
            loadDiaryToEditor(finalDiary);
            loadPopupDiaries();
            
            // 打开日记管理器显示新创建的日记
            const popup = document.getElementById('diary-popup');
            if (popup) {
                popup.classList.add('show');
            }
        });
        
        // 聚焦到日期输入框并选中全部文本
        dateInput.focus();
        const range = document.createRange();
        range.selectNodeContents(dateInput);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }
}

// 添加 deleteDiary 函数
function deleteDiary(id) {
    if (confirm('确定要删除这篇日记吗？')) {
        diaries = diaries.filter(d => d.id !== id);
        const editorContent = document.querySelector('.editor-content');
        
        if (diaries.length === 0) {
            currentDiaryId = null;
            editorContent.innerHTML = '';
            editorContent.classList.add('disabled');
            editorContent.setAttribute('contenteditable', 'false');
            document.getElementById('add-diary-btn').classList.add('glowing');
        } else if (currentDiaryId === id) {
            currentDiaryId = diaries[0].id;
            loadDiaryToEditor(diaries[0]);
        }
        
        saveDiariesToStorage();
        loadPopupDiaries();
    }
}