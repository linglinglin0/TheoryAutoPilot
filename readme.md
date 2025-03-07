# TheoryAutoPilot :rocket:

理论考试全自动答题解决方案，通过智能识别与自动化操作实现高效闯关。

## 核心功能 ✨
- ​**多题型支持**：精准处理判断题、单选题、多选题、填空题
- ​**智能识别系统**：
  - 屏幕OCR文字识别（PixPin+Tesseract）
  - 题目-答案模糊匹配（difflib相似度算法）
  - AI增强解析（集成Kimi大模型）
- ​**自动化操作**：
  - 鼠标/键盘自动化（pyautogui/pydirectinput）
  - 智能选项点击与答案填充
  - 自动提交与错误重试机制
- ​**题库生态**：
  - JSON题库动态更新
  - 题目去重校验
  - 历史答题数据分析

## 技术栈 💻

Python 3.10+ | pyautogui | pytesseract | difflib 
PyWin32 | Pillow | Kimi-API | JSON
## 快速启动 🚀
1. 安装依赖：
```
bash
pip install -r requirements.txt
```
2. PixPin配置：

- 设置区域截图快捷键为 Alt+1
- 设置OCR快捷键为 Shift+C
3. 运行模式：
```
bash
# 自动答题模式（默认10题）
python main.py a --st 1.5 --qn 15

# 题库更新模式
python main.py b
```
## 智能算法流程图
```mermaid
graph TD
    A[触发截图] --> B(OCR识别)
    B --> C{题型判断}
    C -->|判断题| D[坐标分析]
    C -->|选择题| E[模糊匹配]
    C -->|填空题| F[AI生成]
    D/E/F[Pixpin] --> G[自动化操作]
    G --> H[结果反馈]
    H --> I[题库更新]
 ```
注意事项 ⚠️
- 屏幕分辨率建议 1920x1080
- 理论闯关窗口需置顶且保持标准布局
- 首次使用需通过python main.py b初始化题库
- 填空题识别需关闭输入法浮动窗口
## 开源协议
MIT License | 请遵守各平台用户协议合法使用