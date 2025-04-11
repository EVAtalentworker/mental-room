def view_knowledge_base():
    kb_path = 'knowledge_base/mental_health_kb.json'
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
        return kb_data
    except Exception as e:
        print(f"读取知识库失败: {str(e)}")
        return None

# 查看更新后的知识库
kb_data = view_knowledge_base()
if kb_data and 'emotion_management' in kb_data:
    print("情绪管理相关内容已成功添加到知识库")