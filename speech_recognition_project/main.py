import speech_recognition as sr
import pyaudio
import wave
import os
import threading
import pyttsx3  # 添加 pyttsx3 导入
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, flash  # Add flash here
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from run import chat, history
from snownlp import SnowNLP
import json
from collections import Counter
import os
import json
import random
from flask_migrate import Migrate

def load_knowledge_base():
    kb_path = 'knowledge_base/mental_health_kb.json'
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载知识库失败: {str(e)}")
        return {}

def get_response_from_kb(category, kb_data):
    if category in kb_data:
        responses = kb_data[category]['responses']
        suggestions = kb_data[category]['suggestions']
        return {
            'response': random.choice(responses),
            'suggestions': random.sample(suggestions, min(2, len(suggestions)))
        }
    return None

def detect_dangerous_mood(text):
    # 扩展危险词库，按类别组织
    danger_patterns = {
        'severe_danger': [  # 新增严重危险词分类
            '自杀', '轻生', '结束生命', '想死', '不想活',
            '报复社会', '同归于尽', '炸', '枪', '制造混乱',
            '伤害他人', '报仇', '杀人', '毁灭', '爆炸', '开枪'
        ],
        'suicide': [
            '跳楼', '死', '解脱', '活不下去',
            '没有希望', '放弃', '绝望', '伤害自己',
            '割腕', '吃药'
        ],
        'depression': [
            '好累', '没意思', '活着没意义',
            '睡不着', '吃不下', '没胃口', '不想说话',
            '不想动', '提不起劲', '没动力'
        ],
        'anxiety': [
            '焦虑', '紧张', '慌', '喘不过气',
            '心跳好快', '害怕', '恐惧', '担心',
            '压力好大', '受不了了', '快崩溃了'
        ],
        'social': [
            '没人理我', '没人在乎', '好孤独',
            '不想见人', '讨厌社交', '不合群',
            '格格不入', '没人懂我'
        ]
    }
    
    s = SnowNLP(text)
    response_type = 'normal'
    found_keywords = []
    
    # 检查每个类别的关键词
    for category, words in danger_patterns.items():
        for word in words:
            if word in text:
                found_keywords.append({
                    'word': word,
                    'category': category
                })
    
    # 根据找到的关键词和情感分数确定响应类型
    if found_keywords and s.sentiments < 0.3:
        categories = set(item['category'] for item in found_keywords)
        if 'severe_danger' in categories:  # 优先检查严重危险词
            response_type = 'severe_danger'
        elif 'suicide' in categories:
            response_type = 'immediate_danger'
        elif len(categories) >= 2:
            response_type = 'multiple_symptoms'
        else:
            response_type = 'single_symptom'
            
    # 加载知识库
    kb_data = load_knowledge_base()
    
    # 获取知识库的回应
    kb_responses = []
    if found_keywords:
        for category in set(item['category'] for item in found_keywords):
            kb_response = get_response_from_kb(category, kb_data)
            if kb_response:
                kb_responses.append(kb_response)
    
    return {
        'is_dangerous': response_type != 'normal',
        'type': response_type,
        'sentiment_score': s.sentiments,
        'found_keywords': found_keywords,
        'categories': list(set(item['category'] for item in found_keywords)),
        'kb_responses': kb_responses,
        'is_severe': response_type == 'severe_danger'  # 新增严重危险标记
    }
app = Flask(__name__)
speech_recognizer = None
current_stream = None
current_audio = None
frames = []

# 初始化语音引擎
engine = pyttsx3.init()
# 设置中文语音（如果有的话）
voices = engine.getProperty('voices')
for voice in voices:
    if 'chinese' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

# 设置语音属性
engine.setProperty('rate', 180)    # 语速
engine.setProperty('volume', 1.0)  # 音量

# 修改 speak_text 函数
def speak_text(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except RuntimeError:
        # 如果运行循环已经启动，先停止它
        engine.endLoop()
        # 重新初始化引擎
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"语音播放错误: {str(e)}")

class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 44100
        self.chunk = 1024
        self.recording = False
        
    def start_recording(self):
        global current_audio, current_stream, frames
        frames = []
        current_audio = pyaudio.PyAudio()
        
        print("开始录音...")
        current_stream = current_audio.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        self.recording = True
        
        # 开始收集音频数据
        while self.recording:
            if current_stream:
                try:
                    data = current_stream.read(self.chunk)
                    frames.append(data)
                except Exception as e:
                    print(f"录音错误: {str(e)}")
                    break
        
    def stop_recording(self):
        global current_audio, current_stream, frames
        self.recording = False
        
        if current_stream:
            current_stream.stop_stream()
            current_stream.close()
        if current_audio:
            current_audio.terminate()
            
        print("录音结束")
        
        # 保存录音文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(current_audio.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        return filename
        
    def add_audio_data(self):
        global current_stream, frames
        if current_stream:
            data = current_stream.read(self.chunk)
            frames.append(data)

    def transcribe_audio(self, audio_file):
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data, language='zh-CN')
                return text
        except sr.UnknownValueError:
            return "无法识别语音内容"
        except sr.RequestError:
            return "语音识别服务暂时不可用"
        except Exception as e:
            return f"发生错误: {str(e)}"
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/secret')
def secret():
    return render_template('secret.html')

@app.route('/admin')
def admin():
    total_users = User.query.count()
    # 获取发送过危险词的用户数量
    danger_users = User.query.filter(User.has_danger_words == True).count()
    return render_template('admin.html', total_users=total_users, danger_users=danger_users)

@app.route('/other')
def other():
    return render_template('other.html')

@app.route('/qa')
@login_required
def qa():
    return render_template('qa.html')

@app.route('/mood_analysis')
def mood_analysis():
    return render_template('mood_analysis.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global speech_recognizer
    try:
        speech_recognizer.start_recording()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 添加保存数据的函数
# 在文件开头添加所需的导入
from datetime import datetime, timedelta

# 修改保存数据的函数
def save_mood_data(text, sentiment_score, user_id):
    try:
        # 为每个用户创建独立的数据文件
        data_file = f'static/data/mood_data_{user_id}.json'
        
        data = {
            'dangerous_words': {},
            'positive_sentences': [],
            'negative_sentences': [],
            'dates_used': []
        }
        
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # 处理当前用户的数据
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in data['dates_used']:
            data['dates_used'].append(today)
            
        # 检查危险词
        danger_words = [
            '自杀', '跳楼', '结束生命', '死', '解脱',
            '活不下去', '没有希望', '放弃', '绝望',
            '伤害自己', '割腕', '吃药'
        ]
        
        s = SnowNLP(text)
        # 只记录极度积极的句子
        if s.sentiments > 0.9:
            data['positive_sentences'].append(text)
        # 只记录包含危险词且情感消极的句子
        for word in danger_words:
            if word in text and s.sentiments < 0.2:
                data['dangerous_words'][word] = data['dangerous_words'].get(word, 0) + 1
            
        # 保存数据
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"保存数据时出错: {str(e)}")

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        message = data.get('message', '')
        is_voice_mode = data.get('isVoiceMode', False)
        
        # 保存心情数据
        save_mood_data(message, None)
        
        # 检测危险信息
        danger_check = detect_dangerous_mood(message)
        
        # 如果检测到严重危险词，更新用户状态
        if danger_check['is_severe'] and current_user.is_authenticated:
            current_user.has_danger_words = True
            db.session.commit()
        
        # 根据不同类型的症状提供相应的回复
        if danger_check['is_dangerous']:
            if danger_check['kb_responses']:
                # 使用知识库的回应
                kb_response = danger_check['kb_responses'][0]
                response = f"{kb_response['response']}\n\n建议：\n" + \
                          "\n".join(f"- {s}" for s in kb_response['suggestions'])
            elif danger_check['type'] == 'immediate_danger':
                response = f"我注意到你提到了一些令人担忧的话..."
            elif danger_check['type'] == 'multiple_symptoms':
                response = "我感觉你最近的状态不太好，可能遇到了一些困扰。记住，这些感受都是暂时的，如果你愿意，我们可以一起探讨这些问题，或者建议你寻求专业的心理咨询帮助。"
            else:
                response = "我理解你现在的心情可能不太好。有时候和别人分享这些感受，会让自己感觉好一些。要不要告诉我具体发生了什么？"
        else:
            try:
                response = chat(message, history)
                if not response:  # 如果返回为空
                    response = "抱歉，我现在有点忙，请稍后再试。"
            except Exception as e:
                print(f"Chat API 错误: {str(e)}")
                response = "抱歉，我现在有点忙，请稍后再试。"
        
        if is_voice_mode:
            threading.Thread(target=speak_text, args=(response,)).start()
            
        return jsonify({
            'success': True, 
            'response': response,
            'danger_detected': danger_check['is_dangerous'],
            'mood_analysis': danger_check
        })
    except Exception as e:
        print(f"聊天端点错误: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'response': "抱歉，我现在有点忙，请稍后再试。"
        })

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global speech_recognizer
    try:
        audio_file = speech_recognizer.stop_recording()
        text = speech_recognizer.transcribe_audio(audio_file)
        
        # 只返回识别的文本，不直接发送聊天请求
        return jsonify({
            'success': True, 
            'text': text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
        is_voice_mode = request.json.get('isVoiceMode', False)
        
        response = chat(text, history)
        
        if is_voice_mode:
            # 在新线程中播放语音，避免阻塞响应
            threading.Thread(target=speak_text, args=(response,)).start()
            
        return jsonify({'success': True, 'text': text, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mental_diary')
@login_required
def mental_diary():
    return render_template('mental_diary.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# 添加获取数据的路由
@app.route('/get_mood_statistics')
def get_mood_statistics():
    data_file = 'static/data/mood_data.json'
    try:
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 计算使用天数
            if 'dates_used' not in data:
                data['dates_used'] = []
            
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in data['dates_used']:
                data['dates_used'].append(today)
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            data['days_used'] = len(data['dates_used'])
            return jsonify(data)
            
        return jsonify({
            'dangerous_words': {},
            'positive_sentences': [],
            'dates_used': [],
            'days_used': 0
        })
    except Exception as e:
        print(f"读取数据时出错: {str(e)}")
        return jsonify({
            'dangerous_words': {},
            'positive_sentences': [],
            'dates_used': [],
            'days_used': 0
        })

@app.route('/clear_mood_statistics', methods=['POST'])
def clear_mood_statistics():
    try:
        data_file = 'static/data/mood_data.json'
        # 重置数据为空
        empty_data = {
            'dangerous_words': {},
            'positive_sentences': [],
            'negative_sentences': []
        }
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_mood_data', methods=['POST'])
def save_mood_data_endpoint():
    try:
        data = request.get_json()
        text = data.get('text', '')
        mood_data = data.get('mood_data', {})
        
        # 调用现有的保存函数
        save_mood_data(text, mood_data.get('sentiment_score'))
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('用户名或密码错误')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return render_template('register.html')
            
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# 数据库配置（移到这里）
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db.init_app(app)
migrate = Migrate(app, db)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 将这个路由移到其他路由的位置（在 app 定义之后，在 if __name__ == '__main__' 之前）
@app.route('/get_users')
def get_users():
    user_type = request.args.get('type', 'all')
    if user_type == 'danger':
        users = User.query.filter_by(has_danger_words=True).all()
    else:
        users = User.query.all()
    return jsonify([{'username': user.username} for user in users])

if __name__ == "__main__":
    with app.app_context():
        try:
            # 创建数据库表
            db.create_all()
            # 添加 has_danger_words 列
            with db.engine.connect() as conn:
                conn.execute('ALTER TABLE user ADD COLUMN has_danger_words BOOLEAN DEFAULT FALSE')
        except Exception as e:
            print(f"数据库更新错误: {str(e)}")
            
    speech_recognizer = SpeechRecognizer()
    app.run(debug=True)