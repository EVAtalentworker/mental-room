let clickCount = 0;
let lastClickTime = 0;

document.addEventListener('DOMContentLoaded', function() {
    const logo = document.querySelector('.logo');
    
    // 创建提示框函数保持不变
    function createNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            font-size: 14px;
            color: #333;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // 显示动画
        setTimeout(() => notification.style.opacity = '1', 100);
        
        // 3秒后消失
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // 统一处理所有点击事件
    logo.addEventListener('click', async function(e) {
        if (e.target.classList.contains('logo-a')) {
            e.preventDefault();
            const currentTime = new Date().getTime();
            
            if (currentTime - lastClickTime > 3000) {
                clickCount = 1;
            } else {
                clickCount++;
            }
            
            lastClickTime = currentTime;
            console.log('Click count:', clickCount); // 添加调试信息
            
            if (clickCount === 3) {
                window.location.href = '/secret';
                clickCount = 0;
            }
        } else {
            try {
                const response = await fetch('/logout');
                if (response.ok) {
                    createNotification('已退出登录');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                }
            } catch (error) {
                console.error('退出登录失败:', error);
                createNotification('退出登录失败，请重试');
            }
        }
    });
});