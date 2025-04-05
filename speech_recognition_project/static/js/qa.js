document.addEventListener('DOMContentLoaded', function() {
    const recordButton = document.getElementById('recordButton');
    const chatForm = document.getElementById('chatForm');
    const textInput = document.getElementById('textInput');
    const chatContainer = document.getElementById('chat-container');
    const toggleButton = document.getElementById('toggleChatType');
    const chatTypeText = document.getElementById('chatTypeText');
    let isRecording = false;
    let isVoiceMode = false;
    let recordingTimeout = null;  // 添加录音超时控制
    
    // 添加新的全局变量
    let chats = [];
    let currentChatId = null;
    
    // 初始化函数
    // 修改初始化函数
    function initializeChat() {
        // 从 localStorage 加载对话
        const savedChats = localStorage.getItem('chats');
        if (savedChats) {
            chats = JSON.parse(savedChats);
            if (chats.length > 0) {
                currentChatId = chats[0].id;
            } else {
                // 只有当完全没有对话时才创建新对话
                createNewChat();
            }
        } else {
            // 第一次使用时创建新对话
            createNewChat();
        }
        
        if (chats.length > 0) {
            renderChats();
            loadChat(currentChatId);
        }
    }
    
    // 修改创建新对话函数
    function createNewChat() {
        const chatId = Date.now().toString();
        const newChat = {
            id: chatId,
            title: 'New chat',
            messages: []  // 不再添加默认欢迎消息
        };
        chats.unshift(newChat);
        currentChatId = chatId;
        saveChats();
        renderChats();
        loadChat(chatId);
        
        // 只在创建新对话时显示欢迎消息，但不保存到消息历史中
        chatContainer.innerHTML = `
            <div class="message ai-message">
                <div class="message-content">你好！我是你的 AI 语音助手。你可以直接输入文字，或点击下方麦克风按钮进行语音输入。</div>
            </div>
        `;
    }
    
    // 修改清空历史按钮的处理函数
    document.getElementById('clearHistoryButton').addEventListener('click', () => {
        const currentChat = chats.find(c => c.id === currentChatId);
        if (currentChat) {
            currentChat.messages = [];  // 清空消息但不添加欢迎消息
            currentChat.title = 'New chat';
            saveChats();
            loadChat(currentChatId);
            renderChats();
            
            // 显示欢迎消息但不保存
            chatContainer.innerHTML = `
                <div class="message ai-message">
                    <div class="message-content">你好！我是你的 AI 语音助手。你可以直接输入文字，或点击下方麦克风按钮进行语音输入。</div>
                </div>
            `;
        }
    });
    
    function saveChats() {
        localStorage.setItem('chats', JSON.stringify(chats));
    }
    
    function renderChats() {
        const chatList = document.getElementById('chatList');
        chatList.innerHTML = '';
        
        chats.forEach(chat => {
            const chatElement = document.createElement('div');
            chatElement.className = `chat-item ${chat.id === currentChatId ? 'active' : ''}`;
            chatElement.innerHTML = `
                <span class="chat-title">${chat.title}</span>
                <button class="delete-chat" title="删除对话">×</button>
            `;
            
            chatElement.querySelector('.chat-title').addEventListener('click', () => {
                currentChatId = chat.id;
                loadChat(chat.id);
                renderChats();
            });
            
            chatElement.querySelector('.delete-chat').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteChat(chat.id);
            });
            
            chatList.appendChild(chatElement);
        });
    }
    
    function deleteChat(chatId) {
        const index = chats.findIndex(chat => chat.id === chatId);
        if (index !== -1) {
            chats.splice(index, 1);
            if (chats.length === 0) {
                createNewChat();
            } else if (currentChatId === chatId) {
                currentChatId = chats[0].id;
                loadChat(currentChatId);
            }
            saveChats();
            renderChats();
        }
    }
    
    function loadChat(chatId) {
        const chat = chats.find(c => c.id === chatId);
        if (chat) {
            chatContainer.innerHTML = '';
            chat.messages.forEach(msg => {
                addMessage(msg.content, msg.type === 'user');
            });
        }
    }
    
    // 修改原有的 addMessage 函数
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
        messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    
        // 保存消息到当前对话
        const currentChat = chats.find(c => c.id === currentChatId);
        if (currentChat) {
            currentChat.messages.push({
                type: isUser ? 'user' : 'ai',
                content: text
            });
            
            // 如果是用户的第一条消息，更新对话标题
            if (isUser && currentChat.title === 'New chat') {
                currentChat.title = text.length > 20 ? text.substring(0, 20) + '...' : text;
                renderChats();
            }
            
            saveChats();
        }
    }
    
    // 新对话按钮事件处理
    document.getElementById('newChatButton').addEventListener('click', createNewChat);
    
    // 页面加载时初始化
    document.addEventListener('DOMContentLoaded', initializeChat);
    
    // 添加心情关键词检测
    const moodKeywords = {
        '开心': true, '高兴': true, '快乐': true,
        '难过': true, '伤心': true, '悲伤': true,
        '生气': true, '愤怒': true, '烦躁': true,
        '焦虑': true, '担心': true, '害怕': true,
        '平静': true, '放松': true, '满意': true
    };
    
    // 修改心情关键词检测函数
    function detectMood(text) {
        if (!text) return;
        
        for (let mood in moodKeywords) {
            if (text.includes(mood)) {
                // 提取包含心情关键词的完整句子
                const sentences = text.split(/[。！？.!?]/).filter(s => s.trim());
                for (let sentence of sentences) {
                    if (sentence.includes(mood)) {
                        const trimmedSentence = sentence.trim();
                        console.log('正在尝试添加心情:', trimmedSentence); // 调试信息
                        
                        // 确保函数存在后再调用
                        if (typeof window.addMoodFromQA === 'function') {
                            window.addMoodFromQA(trimmedSentence);
                        } else {
                            console.error('addMoodFromQA 函数未找到');
                        }
                    }
                }
            }
        }
    }
    
    // 修改发送消息的事件处理
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = textInput.value.trim();
        if (!text) return;
    
        addMessage(text, true);
        detectMood(text);  // 只检测用户输入的文本
        textInput.value = '';
    
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: text,
                    isVoiceMode: isVoiceMode
                })
            });
            
            const data = await response.json();
            if (data.success) {
                addMessage(data.response);
                // 移除对 AI 回复的心情检测
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('发生错误，请重试');
        }
    });
    
    // 同样修改语音输入部分
    recordButton.addEventListener('click', async () => {
        if (!isRecording) {
            isRecording = true;
            recordButton.classList.add('recording');
            
            try {
                const response = await fetch('/start_recording', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                addMessage('录音出错，请重试');
                recordButton.classList.remove('recording');
                isRecording = false;
            }
        } else {
            try {
                const response = await fetch('/stop_recording', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        isVoiceMode: isVoiceMode
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    // 将识别的文本填入输入框
                    textInput.value = data.text;
                    // 让输入框获得焦点，方便用户编辑
                    textInput.focus();
                    // 将光标移动到文本末尾
                    textInput.setSelectionRange(data.text.length, data.text.length);
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                addMessage('识别出错，请重试');
            } finally {
                recordButton.classList.remove('recording');
                isRecording = false;
            }
        }
    });
    
    // 添加切换按钮的事件监听器
    toggleButton.addEventListener('click', () => {
        isVoiceMode = !isVoiceMode;
        if (isVoiceMode) {
            toggleButton.textContent = '🔈';
            chatTypeText.textContent = '语音对话';
        } else {
            toggleButton.textContent = '📕';
            chatTypeText.textContent = '文字对话';
        }
    });

    // 初始化聊天
    initializeChat();
}); // 添加这个闭合括号