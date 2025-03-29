import speech_recognition as sr
import pyaudio
import wave
import os
import threading
import pyttsx3  # 添加 pyttsx3 导入
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory, request  # 添加 request 导入
from run import chat, history

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

def speak_text(text):
    engine.say(text)
    engine.runAndWait()

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

@app.route('/qa')
def qa():
    return render_template('qa.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global speech_recognizer
    try:
        speech_recognizer.start_recording()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        message = data.get('message', '')
        is_voice_mode = data.get('isVoiceMode', False)
        
        response = chat(message, history)
        
        if is_voice_mode:
            # 在新线程中播放语音，避免阻塞响应
            threading.Thread(target=speak_text, args=(response,)).start()
            
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global speech_recognizer
    try:
        audio_file = speech_recognizer.stop_recording()
        text = speech_recognizer.transcribe_audio(audio_file)
        is_voice_mode = request.json.get('isVoiceMode', False)
        
        response = chat(text, history)
        
        if is_voice_mode:
            # 在新线程中播放语音，避免阻塞响应
            threading.Thread(target=speak_text, args=(response,)).start()
            
        return jsonify({'success': True, 'text': text, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    speech_recognizer = SpeechRecognizer()
    app.run(debug=True)