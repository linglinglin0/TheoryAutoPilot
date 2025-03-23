import argparse
import pandas as pd
import difflib
import pyautogui
import pyscreeze
import pytesseract
import pyperclip
import pydirectinput
import time
from PIL import ImageColor
import re
import json
from kimi import main_kimi
from number_corrected import number_corrected
# 配置PixPin快捷键
SCREENSHOT_HOTKEY = ['alt', '1']  # 区域截图快捷键
OCR_HOTKEY = ['shift', 'c']       # OCR快捷键
submit_HOTKEY = ['tab','space']
# 定义截图区域（根据实际屏幕调整）
import win32clipboard  # 需要安装pywin32
'''
填空题出问题是因为剪贴板和pixpin有冲突
填空题和开不开下面的任务栏有关系
错误处理机制，如果两次检测到的东西相似度很高，就等一下再进行扫描
'''
global_new_questions = []  # 新增全局变量
def copy_text(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()
def paste_text():
    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()
    return data
def trigger_pixpin_screenshot():
    """触发PixPin截图并截取指定区域"""
    # 移动鼠标到区域左上角，确保截图范围正确
    pyautogui.hotkey(*SCREENSHOT_HOTKEY)
    # time.sleep(0.5) # 等待截图工具响应
    # 按下回车确认截图范围
    pyautogui.press('Enter')
    time.sleep(1)  # 等待截图完成

def trigger_pixpin_ocr():
    """触发PixPin的OCR并返回剪贴板内容"""
    pyautogui.hotkey(*OCR_HOTKEY)
    time.sleep(1.5)  # 等待OCR处理
    return paste_text()

def locate(question_type):
    dic = {'判断':'single.png','单选':'single.png','多选':'multiple.png'}
    # 查找屏幕上的图片
    button_location = pyautogui.locateOnScreen(dic[question_type], confidence=0.82)
    if button_location:
        print(f"找到了图片！位置在：{button_location}")
        # 获取图片中心点
        button_center = pyautogui.center(button_location)
        # 返回图片坐标
        asset_x, asset_y = button_center
        return (asset_x, asset_y)
    else:
        print("图片未找到！")
def check_position(text):
    # 初始化位置
    pos_dui = -1  # “对”的位置
    pos_cuo = -1  # “错”的位置

    # 遍历字符串，查找“对”和“错”的位置
    for i, char in enumerate(text):
        if char == '对':
            pos_dui = i
        elif char == '错':
            pos_cuo = i

    # 判断位置关系
    if pos_dui == -1 or pos_cuo == -1:
        # 如果“对”或“错”没有出现
        return "字符串中缺少'对'或'错'"
    elif pos_cuo < pos_dui:
        # “错”出现在“对”之前
        return True
    else:
        # “错”出现在“对”之后
        return False
def is_similar(str1, str2, threshold=0.7):
    # 创建一个SequenceMatcher对象
    matcher = difflib.SequenceMatcher(None, str1, str2)
    similarity_ratio = matcher.ratio()
    return similarity_ratio >= threshold,similarity_ratio
def extract_options(text):
    # 使用正则表达式匹配选项
    pattern = r'([A-D])\.([^\n]+)'
    matches = re.findall(pattern, text)
    
    # 将匹配结果转换为字典
    options_dict = {option: content.strip() for option, content in matches}
    return options_dict
def select_correlation(question_text,test_bank):
    length = len(test_bank)
    max_similarity = 0
    max_index = None
    for i in range(length):
        match,similarity_ratio = is_similar(question_text, test_bank[i]['question_text'])
        if match and similarity_ratio > max_similarity:
            max_similarity = similarity_ratio
            max_index = i
            print(f"找到了更相似的题目,题号为{i+1}：{test_bank[i]['question_text']}")

    if max_index is not None:
            return max_index+1," ".join(test_bank[max_index]['correct_answer'])
    return None,None
def read_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def get_option_coords(option, region):
    """通过Tesseract定位选项标识的坐标"""
    # 截取选项区域
    screenshot = pyautogui.screenshot(region=region)
    # 使用Tesseract识别选项标识及其位置
    data = pytesseract.image_to_data(screenshot, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)
    for i in range(len(data['text'])):
        if data['text'][i].strip() == option:
            x = data['left'][i] + region[0]  # 转换为全局坐标
            y = data['top'][i] + region[1]
            return (x, y)
    return None
def get_key_by_value(my_dict, value):
    for key, val in my_dict.items():
        if val == value:
            return key
    return None  # 如果没有找到匹配的值
def fuzzy_match(answer_text, choices_dict):
    answers = answer_text.split(' ')
    values = choices_dict.values()
    print(values)
    result_keys = []
    for answer in answers:
        # 使用replace 将answer中的空格替换为''
        answer = answer.replace(' ', '')
        print(answer)
        match = difflib.get_close_matches(answer, values, n=1, cutoff=0.6)
        print(match)
        if not match:
            continue
        key = get_key_by_value(choices_dict, match[0])
        result_keys.append(key)
    return result_keys
def find_color_on_screen(color, region=(0, 0, 1920, 1080)):
    """
    在屏幕上查找指定颜色的位置。

    :param color: 要查找的颜色，格式为'#RRGGBB'
    :param region: 可选参数，指定查找的屏幕区域，格式为(left, top, width, height)
    :return: 如果找到颜色，返回颜色的中心位置(x, y)；否则返回None
    """
    # 截取屏幕图像
    screenshot = pyscreeze.screenshot(region=region)
    print('da')
    # 将颜色字符串转换为RGB元组
    color_rgb = ImageColor.getrgb(color)
    print('k')
    # 初始化计数器
    count = 0
    print(screenshot.width)
    # 在截图中查找颜色
    for x in range(screenshot.width):
        for y in range(screenshot.height):
            if screenshot.getpixel((x, y)) == color_rgb:
                # 增加计数器
                count += 1
                # 如果找到10个颜色，返回颜色的中心位置
                if count == 40:
                    return (x+330,y+50)
    print(count)
    return None
def remove_timestamp(text):
    # 使用正则表达式匹配开头的时间信息并去掉
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2} '
    return re.sub(pattern, '', text)
def extract_question(text,quesion_type):
# 第一步：删除指定关键词
    # 处理题目类型
    if quesion_type == '填空':
    # 清理闯关关键词
        for keyword in ['理论闯关', '闯关', '理论闯','里论闯关','论闯关','第1空答案：',' ']:
            text = text.replace(keyword, '')

        # 使用多阶段正则匹配
        pattern = r'''
        第\d+题.*?\n        # 跳过题头行
        (.*?)               # 捕获题目内容
        (?=\n第\d+空答案|提交答案)  # 前瞻断言终止条件
        '''

        # 执行匹配
        match = re.search(pattern, text, re.DOTALL|re.VERBOSE)
        if match:
            # 清理结果
            result = re.sub(r'\n+', '', match.group(1).strip())  # 合并换行符
            result = re.sub(r'，\s*$', '，', result)              # 处理结尾标点
            return result
        else:
            print("未匹配到题目内容")
    else:
# 输出结果：
# 近日，习主席对民政工作作出重要指示，强调中国式现代化，为
        for keyword in ['理论闯关', '闯关', '理论闯','里论闯关','论闯关','仑闯关']:
            text = text.replace(keyword, '')

        # 第二步：删除题头（包括方括号处理）
        text = re.sub(r'^\s*\[?第\d+题.{2}/共10题\]?\s*', '', text, flags=re.MULTILINE)
        # +text = re.sub(r'^\s*$?第\d+题.{2}/共10题$?\s*', '', text, flags=re.MULTILINE)
        # 第三步：提取核心内容并处理D选项后的内容
        pattern = r'''
        ^                     # 从行首开始
        (.*?)                 # 题干部分（非贪婪匹配）
        (                     # 选项部分
            (?:\n[A-D]\..*?)+ # 所有选项
        )
        (?=\n\s*[^\s]|$)      # 前瞻断言确保结束在选项后
        '''

        match = re.search(pattern, text, re.DOTALL|re.VERBOSE)
        if match:
            # 处理D选项后的换行
            result = re.sub(r'(D\..*?)(\n.*)', r'\1', match.group(0), flags=re.DOTALL)
            # 合并多余换行
            result = re.sub(r'\n+', '\n', result).strip()
        else:
            result = text
    # 最后去除result里面的回车
    # result = re.sub(r'\n', '', result)
    return result
def input_string(text):
    """
    使用pyautogui输入指定字符串。

    :param text: 要输入的字符串
    """
    # 等待1秒，确保焦点在正确的位置
    copy_text(text)
    print('粘贴完毕')
    print(paste_text())
    # pyautogui.hotkey('ctrl', 'v')    
    # zhantie = pyperclip.paste()
    # print(f'粘贴内容:{zhantie}')
    
    
    time.sleep(5)
    # 输入字符串


def extract_question_type(text):
    # 使用正则表达式匹配题型信息
    pattern = r"第\d+题(\S+)/共\d+题"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return "未找到题型信息"
import re
import json

def parse_questions(text):
    # 预处理：移除干扰内容并标准化格式
    text = re.sub(r'(已经完成全部.*?今日积分累计已达上限|正确:[0-9]+ / 错误:[0-9]+)', '', text, flags=re.DOTALL)
    text = re.sub(r'\s+', ' ', text).strip()
    # 将回答正确和回答错误都替换为''
    text = re.sub(r'回答正确|回答错误', '', text)
    # 分割题目块（支持多种分隔格式）
    question_blocks = re.split(r'第\d+题\s+', text)[1:]
    
    result = []
    for block in question_blocks:
        try:
            # 提取题型（增强容错）
            q_type_match = re.search(r'(单选题|多选题|填空题)(\s+回答错误)?', block)
            if not q_type_match: continue
            q_type = q_type_match.group(1)
            
            # 分割题干和选项部分
            content_part, options_part = split_components(block, q_type)
            
            # 深度清洗题干
            question_text = clean_content(content_part)
            question_text = remove_timestamp(question_text)
            # 解析选项（增强格式兼容性）
            options = parse_options(options_part,q_type) if q_type != '填空题' else {}
            
            # 提取正确答案（新版精准匹配）
            correct_answer = extract_correct_answer(block, q_type, options)
            
            result.append({
                "question_type": q_type,
                "question_text": question_text,
                "correct_answer": correct_answer
            })
            
        except Exception as e:
            print(f"解析异常：{str(e)}")
            continue
    updata_json(result)
    return result

def split_components(block, q_type):
    """智能分割题干和选项部分"""
    # 填空题特殊处理
    if q_type == '填空题':
        return re.split(r'(第\d+空答案|提交答案)', block)[0], None
    
    # 查找第一个选项的起始位置（兼容多种格式）
    option_start = re.search(r'\b([A-D])\s*[\.．]\s*', block)
    return (block[:option_start.start()].strip(), 
            block[option_start.start():]) if option_start else (block, "")

def clean_content(text):
    """深度清洗题干内容"""
    # 移除题型和状态信息
    text = re.sub(r'(单选题|多选题|填空题)(\s+回答错误)?', '', text)
    # 移除残留选项标记
    return re.sub(r'\s[ABCD]\s?[\.．]?\s*', ' ', text).strip()

def parse_options(text,q_type):
    """解析选项字典（增强空格兼容性）"""
    options = {}
    # 支持"A .内容"、"A．内容"等格式
    # for match in re.finditer(r"([A-D])\s*[\.．]\s*([^\"'\s](?:.*?[^\"'\s])?)", text):
    if q_type == '单选题':
        for match in re.finditer(r"正确选项：\s*([A-D])\s*[\.．]\s*(.*)", text):
            options[match.group(1)] = match.group(2).strip()
    elif q_type == '多选题':
        for match in re.finditer(r"正确选项：\s*([A-D])\s*[\.．]\s*(.*?)\s", text):
            options[match.group(1)] = match.group(2).strip()
    return options

def extract_correct_answer(block, q_type, options):
    """精准提取正确答案（多场景支持）"""
    if q_type == '多选题':
        # 处理多行正确选项声明
        answers = []
        for match in re.finditer(r'正确选项：\s*([A-D])\s*[\.．]?\s*([^\s，]+)', block):
            key = match.group(1)
            if key in options:
                answers.append(options[key])
        return answers if answers else []
    
    if q_type == '填空题':
        match = re.search(r'正确答案：\s*(.*?)\s', block)
        return match.group(1) if match else ""
    # 单选题处理（增强格式匹配）
    match = re.search(r'正确选项：\s*\b([A-D])\b', block)
    if match and (key := match.group(1)) in options:
        return options[key]
    return ""
def extract_wenben(text):
    pattern = r'^(.*?)(?=[A-D]\.)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        wenben_text = match.group(1).strip()
        return wenben_text
    else:
        print("未找到题目文本")
        return text
        
def updata_json(question_dict):
    try:
        with open("questions.json", "r", encoding="utf-8") as json_file:
            questions = json.load(json_file)
    except FileNotFoundError:
        questions = []  # 如果文件不存在，初始化为空列表
    except json.JSONDecodeError:
        print("JSON 格式错误！")
        questions = []  # 如果 JSON 格式错误，初始化为空列表
    # 检查题干是否已存在
    exists = False
    count = 0
    # 遍历question_dict里面的字典，如果题干存在于questions里面  
    # 则说明该题目已经存在，则跳过，否则添加到questions里面
    # 并记录新题目数

    for question_dic in question_dict:
        exists = False
        for question in questions:
            if question["question_text"] == question_dic["question_text"]:
                exists = True
                break
        if not exists:
            questions.append(question_dic)
            count += 1
    try:
        # 将更新后的数据写回到 JSON 文件
        with open("questions.json", "w", encoding="utf-8") as json_file:
            json.dump(questions, json_file, ensure_ascii=False, indent=4)
        print(f"共有{count}个新题目已添加到 JSON 文件！")
    except Exception as e:
        print(f"写入文件时发生错误: {e}")
def update_bank():
    pyautogui.click(x=710,y=826)
    time.sleep(0.5)
    pyautogui.click(x=710,y=867)
    pydirectinput.keyDown('ctrl')
    pydirectinput.press('a')
    pydirectinput.keyUp('ctrl')
    time.sleep(0.5)
    pydirectinput.keyDown('ctrl')
    pydirectinput.press('c')
    pydirectinput.keyUp('ctrl')
    time.sleep(0.5)
    clipboard_text = paste_text()
    # 解析题目
    question_dict = parse_questions(clipboard_text)
    # 写入题库
    updata_json(question_dict)
    number_corrected()
    print("题库更新完成！")
def drag_copy():
    # pyautogui 实现从1286,1178到1492,1178拖拽
    pyautogui.click(1286, 1541)
    pyautogui.dragTo(1492, 1541, 0.5)
    # 按下ctrl+c
    pydirectinput.keyDown('ctrl')
    pydirectinput.press('c')
    pydirectinput.keyUp('ctrl')
    time.sleep(0.5)
    # 粘贴
    x,y = find_color_on_screen('#FCF8E3')
    pyautogui.click(x, y)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)

def get_four_option_question_numbers():
    """
    该函数用于从 JSON 文件中读取题库数据，找出有四个选项的题目编号。

    返回:
        list: 包含有四个选项的题目编号的列表。
    """
    # 读取 JSON 文件
    with open('c:/Users/user/Desktop/auto_lilun/questions.json', 'r', encoding='utf-8') as file:
        questions = json.load(file)

    # 初始化一个空列表，用于存储有四个选项的题目编号
    four_option_question_numbers = []

    # 遍历每个题目
    for question in questions:
        # 检查正确答案列表的长度是否为 4
        if len(question['correct_answer']) == 4:
            # 如果是，则将该题目的编号添加到列表中
            four_option_question_numbers.append(question['number'])

    return four_option_question_numbers

# 调用函数并打印结果
result = get_four_option_question_numbers()
print(result)

def main():
    # Step 1: 识别题目
    trigger_pixpin_screenshot()
    question_text = trigger_pixpin_ocr()
    question_type = extract_question_type(question_text)
    print("题型:", question_type)
    if question_type == '判断':
        # 定位题目图片并点击
        asset_x, asset_y = locate(question_type)
        # 在question_text中查找‘错’出现在‘对’前面还是后面
        if check_position(question_text) == True:
            pyautogui.click(x=asset_x+114, y=asset_y)
        else:
            pyautogui.click(x=asset_x, y=asset_y)
        pydirectinput.press('tab')
        pydirectinput.press('space')
    elif question_type == '填空':
        question_text = extract_question(question_text,question_type)
        answer_text = select_correlation(question_text,read_json_file('questions.json'))
        if answer_text == None:
            ask_text = '请在下面的横线中填入正确的内容，只输出答案。'+ question_text
            # time.sleep(1)
            answer_text,cost = main_kimi(ask_text)
            print('kimi模型输出的答案为：')
        print(answer_text[1])
        # 定位题目图片并点击
        drag_copy()
        # 粘贴
        pydirectinput.press('tab')
        pydirectinput.press('space')
    else:
        question_text = extract_question(question_text,question_type)
        asset_x, asset_y = locate(question_type)
        wenben_text = extract_wenben(question_text)
        question_num,answer_text = select_correlation(wenben_text,read_json_file('questions.json'))
        choices_dic = extract_options(question_text)
        result_4choices_qn = get_four_option_question_numbers()
        print(f"清洗后的题目文本：{wenben_text}")
        print(f"选项字典：{choices_dic}")
        print(f"题目答案：{answer_text}")
        # 定位题目图片并点击
        if question_type == '多选':
            dic_single = {'A':(asset_x,asset_y),'B':(asset_x+130,asset_y),'C':(asset_x+2*130,asset_y),'D':(asset_x+3*130,asset_y)}
        else:
            dic_single = {'A':(asset_x,asset_y),'B':(asset_x+114,asset_y),'C':(asset_x+2*114,asset_y),'D':(asset_x+3*114,asset_y)}
        try:
            if question_num in result_4choices_qn:
                result_keys = ['A','B','C','D']
            elif question_num!= None and question_num == 158:
                result_keys = ['A','B','C']
            elif question_num!= None and question_num == 168:
                result_keys = ['A','B','C']
            elif question_num!= None and question_num == 202:
                result_keys = ['A','B','D']
            elif question_num!= None and question_num == 119:
                result_keys = ['A','B','C']
            elif question_num!= None and question_num == 285:
                result_keys = ['A','B','C']
            elif question_num!= None and question_num == 128:
                result_keys = ['A','B','C']
            elif question_num!= None and question_num == 121:
                result_keys = ['A','B','C']
            elif question_num!= None and question_num == 53:
                result_keys = ['A','C','D']
            elif question_num!= None and question_num == 263:
                result_keys = ['A','C','D']
            elif question_num!= None and question_num == 61:
                result_keys = ['A']
            elif question_num!= None and question_num == 251:
                result_keys = ['D']
            elif question_num!= None and question_num == 63:
                result_keys = ['B','C','D']
            elif question_num!= None and question_num == 25:
                result_keys = ['A','B','D']
            elif question_num!= None and question_num == 96:
                result_keys = ['A','B','D']
            elif question_num!= None and question_num == 155:
                result_keys = ['A','B','D']
            elif question_num!= None and question_num == 167:
                result_keys = ['A','B','D']
            elif question_num!= None and question_num == 180:
                result_keys = ['B','C']
            elif question_num!= None and question_num == 221:
                result_keys = ['C']
            elif question_num!= None and question_num == 22:
                result_keys = ['C']
            elif question_num!= None and question_num == 78:
                result_keys = ['A']
            elif question_num!= None and question_num == 62:
                result_keys = ['D']
            elif question_num!= None and question_num == 172:
                result_keys = ['D']
            elif question_num!= None and question_num == 264:
                result_keys = ['A','B']
            elif question_num!= None and question_num == 70:
                result_keys = ['B','D']
            elif question_num!= None and question_num == 210:
                result_keys = ['A','B','C']
            elif question_num!= None and question_num == 199:
                result_keys = ['A','C']
            elif question_num!= None and question_num == 243:
                result_keys = ['B','C']
            elif question_num!= None and question_num == 132:
                result_keys = ['B']
            elif question_num!= None and question_num == 275:
                result_keys = ['B']
            else:
                result_keys = fuzzy_match(answer_text, choices_dic) 
            
        except:
            print('程序匹配到的选项为空，请检查题目选项是否正确')
            ask_text = '请填写下面文字中括号内的内容，只输出答案,如果有多个答案，请用空格分隔。要求给出的答案放在原句子中要能在联网搜索中找到完全相同的句子。请填写下面文字中括号内的内容，' \
                        '只输出答案不要输出‘ABCD’,如果有多个答案，请用空格分隔。要求给出的答案放在原句子中要能在联网搜索中找到完全相同的句子。同时，我这里有四个备选选项' \
                        + str(choices_dic.values()) + question_text
            # time.sleep(2)
            answer_text, cost = main_kimi(ask_text)
            print('kimi模型输出的答案为：',answer_text)
            result_keys = fuzzy_match(answer_text, choices_dic)
            print('根据程序匹配到的选项为：')
            print(result_keys)
            # 新增代码：保存题目和答案到临时列表
            new_question = {
                "question_type": question_type,
                "question_text": wenben_text,
                "correct_answer": [choices_dic[key] for key in result_keys if key in choices_dic]
            }
            global global_new_questions
            global_new_questions.append(new_question)

        if 'A' in result_keys:
            pyautogui.click(dic_single['A'])
            count = 4
            # time.sleep(0.1)
        if 'B' in result_keys:
            pyautogui.click(dic_single['B'])
            count = 3
            # time.sleep(0.1)
        if 'C' in result_keys:
            pyautogui.click(dic_single['C'])
            count = 2
            # time.sleep(0.1)
        if 'D' in result_keys:
            pyautogui.click(dic_single['D'])
            count = 1
            # time.sleep(0.1)
        if question_type == '多选':
            print('最终的count为：',count)
            for i in range(count):
                pydirectinput.press('tab')
                # time.sleep(0.1)
        else:
            pydirectinput.press('tab')
            # time.sleep(0.3)
        pydirectinput.press('space')
        # time.sleep(0.5)
def cmd_main():
    parser = argparse.ArgumentParser(description='处理命令行参数')
    parser.add_argument('action', choices=['a', 'b'], help='要执行的操作')
    parser.add_argument('--st', type=float, default=1, help='做题时每次操作间隔时间（秒），默认为1s')
    parser.add_argument('--qn', type=int, default=10, help='要回答的题目数量，默认为10')
    args = parser.parse_args()

    if args.action == 'a':
        print("执行完整程序")
        for i in range(args.qn):
            main()
            time.sleep(args.st)
            print(f'第{i + 1}题完成\n')
        updata_json(global_new_questions)
        number_corrected()
        print("题库更新完成！")
    elif args.action == 'b':
        print("执行更新题库")
        update_bank()

if __name__ == "__main__":
    cmd_main()
# 命令行使用示例
'''
使用示例：
执行 10 题，每次间隔 1 秒：

bash
python main.py a

执行 20 题，每次间隔 2 秒：

bash
python main.py a --st 2 --qn 20

更新题库：
bash
python main.py b
'''
