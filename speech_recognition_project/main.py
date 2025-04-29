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
from run import chat, history
from snownlp import SnowNLP
import json
import random
from flask_migrate import Migrate
from datetime import datetime, timedelta
from models import db, User, Symptom, UserSymptom, Solution

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
    # 修改危险词检测逻辑
    danger_patterns = {
        'severe_danger': set([
            '自杀', '轻生', '结束生命', '想死', '不想活',
            '报复社会', '同归于尽', '炸', '枪', '制造混乱',
            '伤害他人', '报仇', '杀人', '毁灭', '爆炸', '开枪'
        ]),
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
    
    # 添加隐患特征检测
    risk_patterns = {
        'behavior_changes': [
            '睡眠变化', '食欲改变', '不想吃饭', '睡不着', '总是睡觉',
            '情绪波动', '暴躁', '易怒', '心情起伏', 
            '不想社交', '不想见人', '退出社团', '不参加活动',
            '成绩下降', '工作效率低', '无法集中注意力'
        ],
        'cognitive_changes': [
            '记忆力差', '思维混乱', '无法思考', '注意力不集中',
            '对声音敏感', '对光敏感', '感觉不真实', 
            '失去动力', '提不起劲', '没有兴趣'
        ],
        'social_changes': [
            '旷课', '旷工', '人际关系', '同事关系', '同学关系',
            '觉得被监视', '觉得被跟踪', '觉得不安全'
        ]
    }
    
    # 检查隐患特征
    risk_found = False
    for category, patterns in risk_patterns.items():
        for pattern in patterns:
            if pattern in text:
                risk_found = True
                break
        if risk_found:
            break
    
    return {
        'is_dangerous': response_type != 'normal',
        'is_risk': risk_found,  # 添加隐患标记
        'type': response_type,
        'sentiment_score': s.sentiments,
        'found_keywords': found_keywords,
        'categories': list(set(item['category'] for item in found_keywords)),
        'kb_responses': kb_responses,
        'is_severe': response_type == 'severe_danger'
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
        # 调整音频参数以减少处理负担
        self.chunk = 2048  # 增加chunk大小
        self.sample_rate = 16000  # 降低采样率，16kHz足够语音识别
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

# 修改保存数据的函数
def save_mood_data(text, sentiment_score, user_id=None):
    try:
        data_file = 'static/data/mood_data.json'
        if user_id:
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
@login_required
def chat_endpoint():
    try:
        # 添加数据库会话管理
        db_session = db.session()
        try:
            data = request.get_json()
            message = data.get('message', '')
            is_voice_mode = data.get('isVoiceMode', False)
            
            # 检查用户是否登录
            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'error': '请先登录'
                })
            
            # 使用全局历史记录
            response = chat(message, history)
            
            # 检测危险信息
            danger_check = detect_dangerous_mood(message)
            
            # 更新用户状态
            if danger_check['is_dangerous'] or danger_check['is_severe']:
                user = db_session.query(User).get(current_user.id)
                user.has_danger_words = True
                user.danger_word_count = user.danger_word_count + 1
                user.last_danger_time = datetime.now()
                
                # 如果是严重危险词
                if danger_check['is_severe']:
                    user.severe_danger_count = user.severe_danger_count + 1
                
                # 更新危险等级
                if user.severe_danger_count > 0:
                    user.danger_level = 'severe'
                elif user.danger_word_count >= 3:
                    user.danger_level = 'high'
                else:
                    user.danger_level = 'medium'
                    
                db_session.add(user)
                
                # 记录危险行为
                danger_record = DangerRecord(
                    user_id=current_user.id,
                    content=message,
                    danger_type='severe' if danger_check['is_severe'] else 'normal',
                    detected_words=','.join([kw['word'] for kw in danger_check['found_keywords']]),
                    sentiment_score=danger_check['sentiment_score']
                )
                db_session.add(danger_record)
                db_session.commit()
                
            elif danger_check['is_risk']:
                user = User.query.get(current_user.id)
                user.has_risk_signs = True
                user.risk_count = user.risk_count + 1
                user.last_risk_time = datetime.now()
                
                # 记录风险行为
                risk_record = RiskRecord(
                    user_id=current_user.id,
                    content=message,
                    risk_type=danger_check['categories'][0] if danger_check['categories'] else 'unknown',
                    detected_patterns=','.join([kw['word'] for kw in danger_check['found_keywords']]),
                    sentiment_score=danger_check['sentiment_score']
                )
                db_session.add(risk_record)
                db_session.commit()
            
            # 保存心情数据
            save_mood_data(message, None, current_user.id)
            
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
                    response = "感觉到你最近的状态不太好，可能遇到了一些困扰。记住，这些感受都是暂时的，如果你愿意，我们可以一起探讨这些问题，或者建议你寻求专业的心理咨询帮助。"
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
        finally:
            db_session.close()
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
        
        return jsonify({
            'success': True, 
            'text': text
        })
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
@login_required
def clear_mood_statistics():
    try:
        data_file = f'static/data/mood_data_{current_user.id}.json'
        # 重置数据为空
        empty_data = {
            'dangerous_words': {},
            'positive_sentences': [],
            'negative_sentences': []
        }
        
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
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
        
        # 调用现有的保存函数，添加默认的 user_id 参数
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

# 数据库配置 - 移到这里
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///c:/Users/nbsmd/Desktop/speech_recognition_project/instance/users.db'
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

@app.route('/get_users')
def get_users():
    user_type = request.args.get('type', 'all')
    if user_type == 'danger':
        # 危险用户判定：同时满足多个条件
        dangerous_users = User.query.filter(
            db.and_(
                User.has_danger_words == True,
                db.or_(
                    User.severe_danger_count > 0,  # 出现过严重危险词
                    User.danger_word_frequency >= 3,  # 危险词出现频率较高
                    User.average_sentiment < 0.2  # 情感值持续低迷
                )
            )
        ).all()
        return jsonify([{'username': user.username} for user in dangerous_users])
    
    elif user_type == 'risk':
        # 隐患用户判定：满足任一组行为模式
        risk_users = User.query.filter(
            db.or_(
                # 行为变化模式
                db.and_(
                    User.behavior_changes == True,
                    User.behavior_duration >= timedelta(days=7)  # 持续时间超过7天
                ),
                # 认知变化模式
                db.and_(
                    User.cognitive_changes == True,
                    User.cognitive_frequency >= 3  # 出现频率较高
                ),
                # 社交变化模式
                db.and_(
                    User.social_changes == True,
                    User.social_isolation_days >= 5  # 社交隔离天数
                )
            )
        ).all()
        return jsonify([{'username': user.username} for user in risk_users])
    
    else:
        users = User.query.all()
        return jsonify([{'username': user.username} for user in users])

@app.route('/get_user_details/<username>')
def get_user_details(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
        
    # 获取用户的症状记录
    user_symptoms = UserSymptom.query.filter_by(user_id=user.id).all()
    symptoms = []
    solutions = []
    
    for user_symptom in user_symptoms:
        symptom = Symptom.query.get(user_symptom.symptom_id)
        if symptom:
            symptoms.append({
                'name': symptom.name,
                'frequency': user_symptom.frequency
            })
            # 获取该症状的解决方案
            symptom_solutions = get_solutions(symptom.id)
            solutions.extend(symptom_solutions)
    
    return jsonify({
        'username': username,
        'symptoms': symptoms,
        'solutions': list(set(solutions))  # 去重
    })

@app.route('/get_user_basic_info/<username>')
def get_user_basic_info(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
        })
    except Exception as e:
        print(f"Error in get_user_basic_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_user_symptoms/<username>')
def get_user_symptoms(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        # 获取用户症状记录
        user_symptoms = UserSymptom.query.filter_by(user_id=user.id).all()
        symptoms = []
        for us in user_symptoms:
            symptom = Symptom.query.get(us.symptom_id)
            if symptom:
                symptoms.append({
                    'name': symptom.name,
                    'description': symptom.description,
                    'detected_at': us.detected_at.strftime('%Y-%m-%d %H:%M:%S')
                })
                
        return jsonify({
            'symptoms': symptoms,
            'last_check_time': max([s['detected_at'] for s in symptoms]) if symptoms else '暂无记录'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    with app.app_context():
        try:
            # 只创建不存在的表，不删除现有数据
            db.create_all()
        except Exception as e:
            print(f"数据库更新错误: {str(e)}")
            
    speech_recognizer = SpeechRecognizer()
    app.run(debug=True)


def identify_symptoms(text, user_id):
    # 症状模式匹配字典
    symptom_patterns = {
        '抑郁症状': [
            '情绪低落', '兴趣减退', '睡眠问题', '疲劳', '无价值感',
            '注意力难以集中', '食欲改变', '自责', '绝望'
        ],
        '焦虑症状': [
            '紧张', '担心', '坐立不安', '易怒', '注意力难以集中',
            '肌肉紧张', '睡眠障碍', '心悸', '出汗'
        ],
        '社交恐惧': [
            '社交回避', '害怕与人交往', '社交场合紧张', '担心被评判',
            '公众场合焦虑', '回避眼神接触'
        ],
        '强迫症状': [
            '反复检查', '重复行为', '侵入性想法', '清洁强迫',
            '对称需求', '计数行为'
        ]
    }

    detected_symptoms = []
    
    # 检查文本中的症状
    for symptom_type, patterns in symptom_patterns.items():
        for pattern in patterns:
            if pattern in text:
                # 查找或创建症状记录
                symptom = Symptom.query.filter_by(name=symptom_type).first()
                if not symptom:
                    symptom = Symptom(name=symptom_type)
                    db.session.add(symptom)
                
                # 记录用户症状
                user_symptom = UserSymptom.query.filter_by(
                    user_id=user_id,
                    symptom_id=symptom.id
                ).first()
                
                if user_symptom:
                    user_symptom.frequency += 1
                else:
                    user_symptom = UserSymptom(
                        user_id=user_id,
                        symptom_id=symptom.id
                    )
                    db.session.add(user_symptom)
                
                detected_symptoms.append({
                    'type': symptom_type,
                    'pattern': pattern
                })
    
    if detected_symptoms:
        db.session.commit()
    
    return detected_symptoms

def get_solutions(symptom_id):
    """获取针对特定症状的解决方案"""
    solutions = Solution.query.filter_by(symptom_id=symptom_id)\
        .order_by(Solution.priority.desc())\
        .all()
    return [solution.content for solution in solutions]

# 添加数据库连接池配置
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30