import pyautogui
import time
import json
import pyperclip
import keyboard


def write_text(text):
    for char in text:
        keyboard.press(char)
        keyboard.release(char)
        time.sleep(0.05)  # 添加适当的延时，避免过快输入

def init_pw(account, password):
    # 假设已经手动将焦点切换到包含文本框的窗口
    # 等待一段时间，确保你有足够的时间切换到目标窗口
    pyautogui.click(813, 528)
    time.sleep(0.5)
    for _ in range(15):
        keyboard.press('backspace')
        keyboard.release('backspace')
    time.sleep(0.1)
    write_text(account)
    time.sleep(0.5)
    pyautogui.click(789, 612)
    write_text(password)
    # 模拟按下 Tab 键切换到登陆按钮
    pyautogui.press('tab')
    time.sleep(0.5)
    pyautogui.press('enter')

def select_and_login():
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
            accounts = config.get('accounts', [])

            if accounts:
                print("可用的账号列表:")
                for i, account_info in enumerate(accounts, start=1):
                    account = account_info.get('account')
                    print(f"{i}. {account}")

                try:
                    choice = int(input("请输入要使用的账号序号: "))
                    if 1 <= choice <= len(accounts):
                        selected_account_info = accounts[choice - 1]
                        account = selected_account_info.get('account')
                        password = selected_account_info.get('password')
                        if account and password:
                            print(f"正在使用账号 {account} 进行登录...")
                            init_pw(account, password)
                        else:
                            print("选中的账号信息不完整，请检查配置文件。")
                    else:
                        print("输入的序号无效，请输入有效的账号序号。")
                except ValueError:
                    print("输入无效，请输入一个有效的整数序号。")
            else:
                print("配置文件中未找到账号信息。")
    except FileNotFoundError:
        print("未找到配置文件，请创建 config.json 文件并添加账号和密码信息。")
    except json.JSONDecodeError:
        print("配置文件格式错误，请检查 JSON 格式。")

# 调用封装好的函数
if __name__ == "__main__":
    select_and_login()