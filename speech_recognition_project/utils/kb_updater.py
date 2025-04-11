from text_processor import process_article
from kb_manager import update_knowledge_base

# 修改文件路径
with open('articles/anger1.txt', 'r', encoding='utf-8') as f:
    article = f.read()

# 处理文章内容
anger_data = {
    'responses': [
        "我们一起做深呼吸，这样可以帮助我们平静下来",
        "我理解你现在感到愤怒，这是正常的感受",
        "你做得很好，我看到你在努力控制情绪",
        "用语言表达比行为表达更有效"
    ],
    'suggestions': [
        "进行深呼吸练习",
        "使用积极的自我对话",
        "画出让你感到平静的地方",
        "学习识别和表达情绪",
        "适度运动释放情绪",
        "必要时寻求专业帮助"
    ],
    'symptoms': [
        "情绪暴躁",
        "易怒",
        "攻击性行为",
        "无法控制愤怒",
        "经常发脾气"
    ]
}

# 更新知识库
update_knowledge_base('anger_management', anger_data)