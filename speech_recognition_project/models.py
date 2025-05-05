from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class DangerRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    danger_type = db.Column(db.String(50))
    detected_words = db.Column(db.Text)
    sentiment_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RiskRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    risk_type = db.Column(db.String(50))
    detected_patterns = db.Column(db.Text)
    sentiment_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    has_danger_words = db.Column(db.Boolean, default=False)
    danger_word_count = db.Column(db.Integer, default=0)
    severe_danger_count = db.Column(db.Integer, default=0)
    danger_level = db.Column(db.String(20), default='normal')
    has_risk_signs = db.Column(db.Boolean, default=False)
    risk_count = db.Column(db.Integer, default=0)
    last_danger_time = db.Column(db.DateTime)
    last_risk_time = db.Column(db.DateTime)
    average_sentiment = db.Column(db.Float, default=0.5)
    last_check_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 隐患用户相关字段
    behavior_changes = db.Column(db.Boolean, default=False)
    behavior_start_date = db.Column(db.DateTime)
    cognitive_changes = db.Column(db.Boolean, default=False)
    cognitive_frequency = db.Column(db.Integer, default=0)
    social_changes = db.Column(db.Boolean, default=False)
    social_isolation_days = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_user_status(self):
        """获取用户状态信息，不影响现有判断逻辑"""
        status = {
            'is_danger': self.has_danger_words,
            'is_risk': self.has_risk_signs,
            'details': []
        }
        
        # 补充危险用户详情
        if self.has_danger_words:
            details = []
            if self.severe_danger_count > 0:
                details.append(f'严重危险词出现次数：{self.severe_danger_count}')
            if self.danger_word_frequency > 0:
                details.append(f'危险词频率：{self.danger_word_frequency}')
            if self.average_sentiment < 0.5:
                details.append(f'情感值：{self.average_sentiment:.2f}')
            status['details'].extend(details)
        
        # 补充隐患用户详情
        if self.has_risk_signs:
            details = []
            if self.behavior_changes and self.behavior_start_date:
                details.append('行为变化')
            if self.cognitive_changes:
                details.append(f'认知问题（频率：{self.cognitive_frequency}）')
            if self.social_changes:
                details.append(f'社交隔离（{self.social_isolation_days}天）')
            status['details'].extend(details)
            
        return status

    def update_risk_status(self, check_result):
        """更新用户风险状态，保持与现有逻辑兼容"""
        if check_result.get('danger_words'):
            self.has_danger_words = True
            self.danger_word_frequency += 1
        
        if check_result.get('risk_signs'):
            self.has_risk_signs = True
            
        self.last_check_date = datetime.utcnow()

# 其他模型保持不变
class Symptom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    severity_level = db.Column(db.Integer, default=1)  # 1-5，表示症状严重程度

class UserSymptom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptom.id'), nullable=False)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    frequency = db.Column(db.Integer, default=1)  # 症状出现频率

class Solution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptom.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, default=1)  # 解决方案优先级