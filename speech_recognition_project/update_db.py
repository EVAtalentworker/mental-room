from flask import Flask
from models import db, User, DangerRecord, RiskRecord  # 添加新的模型导入
import sqlite3
import os
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///c:/Users/nbsmd/Desktop/speech_recognition_project/instance/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def update_database():
    with app.app_context():
        try:
            db_path = 'c:/Users/nbsmd/Desktop/speech_recognition_project/instance/users.db'
            backup_path = 'c:/Users/nbsmd/Desktop/speech_recognition_project/instance/users_backup.db'
            
            # 创建备份
            if os.path.exists(db_path):
                import shutil
                shutil.copy2(db_path, backup_path)
                print("已创建数据库备份")
            
            # 确保所有连接关闭
            db.session.remove()
            db.session.close_all()
            
            # 删除并重建数据库
            if os.path.exists(db_path):
                os.remove(db_path)
                print("已删除旧数据库")
            
            # 重新创建数据库
            db.create_all()
            
            print("正在验证数据库结构...")
            # 验证新数据库结构
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print("\n创建的表：")
            for table in tables:
                print(f"\n表 {table[0]} 的结构：")
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"- {col[1]} ({col[2]})")
            
            conn.close()
            print("\n数据库更新完成！")
            
        except Exception as e:
            print(f"更新失败: {str(e)}")
            # 如果失败，恢复备份
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, db_path)
                print("已恢复数据库备份")

if __name__ == "__main__":
    # 确保完全关闭之前的连接
    time.sleep(2)
    update_database()