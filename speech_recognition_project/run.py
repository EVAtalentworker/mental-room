import os
from dotenv import load_dotenv
import sys
import time
import threading
import httpx
from openai import OpenAI

load_dotenv()

# 添加全局变量
loading_done = False
history = []  # 添加历史记录列表

# 创建自定义的 httpx 客户端
http_client = httpx.Client(
    base_url="https://api.moonshot.cn/v1",
    timeout=60.0
)

client = OpenAI(
    api_key="sk-tTIHqfyUOzhhw6lk7ig6qSUSlTy8xsDXC87ntzVTr2dQwqtn",  # 请替换为你的有效 Moonshot API key
    http_client=http_client,
    base_url="https://api.moonshot.cn/v1"  # 添加 base_url
)

def loading_animation():
    animation = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    idx = 0
    while not loading_done:
        print(f"\r思考中 {animation[idx % len(animation)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)

class ChatHistory:
    def __init__(self):
        self.histories = {}  # 用字典存储每个用户的聊天历史
        
    def get_history(self, user_id):
        if user_id not in self.histories:
            self.histories[user_id] = []
        return self.histories[user_id]
        
    def add_message(self, user_id, message):
        if user_id not in self.histories:
            self.histories[user_id] = []
        self.histories[user_id].append(message)
        
    def clear_history(self, user_id):
        self.histories[user_id] = []

# 创建全局聊天历史管理器
chat_history = ChatHistory()

def chat(query, history):
    global loading_done
    loading_done = False
    max_retries = 3
    retry_delay = 1
    
    animation_thread = threading.Thread(target=loading_animation)
    animation_thread.daemon = True
    animation_thread.start()
    
    try:
        history.append({"role": "user", "content": query})
        
        for attempt in range(max_retries):
            try:
                completion = client.chat.completions.create(
                    model="moonshot-v1-8k",
                    messages=history,
                    temperature=0.3,
                    stream=True
                )
                
                loading_done = True
                animation_thread.join()
                sys.stdout.write('\r' + ' ' * 20 + '\r')
                sys.stdout.flush()
                
                result = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        result += content
                
                history.append({"role": "assistant", "content": result})
                return result
                
            except Exception as e:
                if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                    print(f"\n遇到速率限制，等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise e
                    
    except Exception as e:
        loading_done = True
        animation_thread.join()
        sys.stdout.write('\r' + ' ' * 20 + '\r')
        sys.stdout.flush()
        return f"发生错误: {e}"