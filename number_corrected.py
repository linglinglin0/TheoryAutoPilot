# 读取questions.json文件，会得到一个列表 ，列表中储存着很多字典，每个字典代表一个问题，给每个字典增加一个number键对应其编号，并将其写入到新的questions.json文件中。
import json
def number_corrected():
    with open('questions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for i, question in enumerate(data):
        question['number'] = i + 1

    # 还要完成一个任务是检测每个字典中correct_anwser键对应的值的类型都要为list，如果不是list，则将其转换为list。
    for question in data:
        if not isinstance(question['correct_answer'], list):
            question['correct_answer'] = [question['correct_answer']]
    with open('questions.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)