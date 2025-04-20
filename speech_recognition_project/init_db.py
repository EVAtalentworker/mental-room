from main import app
from models import db, Symptom, Solution

def init_solutions():
    with app.app_context():
        # 清空现有数据
        Solution.query.delete()
        Symptom.query.delete()
        
        # 创建症状和解决方案
        symptoms_solutions = {
            '抑郁症状': [
                '建议寻求专业心理咨询帮助',
                '保持规律的作息时间',
                '进行适度的运动',
                '与亲友保持联系',
                '学习放松技巧'
            ],
            '焦虑症状': [
                '练习深呼吸和冥想',
                '进行渐进性肌肉放松训练',
                '保持规律运动',
                '避免咖啡因等刺激物',
                '建立健康的生活方式'
            ],
            # ... 其他症状和解决方案
        }
        
        for symptom_name, solutions in symptoms_solutions.items():
            symptom = Symptom(name=symptom_name)
            db.session.add(symptom)
            db.session.flush()
            
            for priority, solution_content in enumerate(solutions, 1):
                solution = Solution(
                    symptom_id=symptom.id,
                    content=solution_content,
                    priority=priority
                )
                db.session.add(solution)
        
        db.session.commit()

if __name__ == '__main__':
    init_solutions()