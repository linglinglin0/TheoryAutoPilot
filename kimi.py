from typing import *
import os
import json
import time
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
import requests

client = OpenAI(
    base_url="https://api.moonshot.cn/v1",
    api_key="sk-Iltcqs7C93z0ov0k7baZmgVaorJWEzeWEfls6ieOfEwXusXc"
)

# search 工具的具体实现，这里我们只需要返回参数即可
def search_impl(arguments: Dict[str, Any]) -> Any:
    """
    在使用 Moonshot AI 提供的 search 工具的场合，只需要原封不动返回 arguments 即可，
    不需要额外的处理逻辑。

    但如果你想使用其他模型，并保留联网搜索的功能，那你只需要修改这里的实现（例如调用搜索
    和获取网页内容等），函数签名不变，依然是 work 的。

    这最大程度保证了兼容性，允许你在不同的模型间切换，并且不需要对代码有破坏性的修改。
    """
    return arguments

def chat(messages) -> Choice:
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            completion = client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=messages,
                temperature=0.8,
                tools=[
                    {
                        "type": "builtin_function",  # <-- 使用 builtin_function 声明 $web_search 函数，请在每次请求都完整地带上 tools 声明
                        "function": {
                            "name": "$web_search",
                        },
                    }
                ]
            )
            return completion.choices[0]
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries < max_retries:
                wait_time = 3 ** retries  # 指数退避策略
                print(f"Request failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Max retries exceeded: {e}")
                raise

def estimate_token_count(messages):
    contents = messages[3]['content']
    # 把contents从 string 类型变成字典
    contents = json.loads(contents)
    total_tokens = contents['usage']['total_tokens']
    cost = calculate_cost(total_tokens)
    return total_tokens, cost

def calculate_cost(total_tokens):
    # 收费标准：1M tokens = ￥12.00
    tokens_per_mill = 1000000
    cost_per_mill = 12.00
    # 计算花费
    cost = (total_tokens / tokens_per_mill) * cost_per_mill
    cost = 0.03 + cost
    return round(cost, 2)  # 保留两位小数

def main_kimi(input_content):
    messages = [
        {"role": "system", "content": "你是kimi"},
    ]

    # 初始提问
    messages.append({
        "role": "user",
        "content": f"{input_content}",
    })

    finish_reason = None
    while finish_reason is None or finish_reason == "tool_calls":
        choice = chat(messages)
        finish_reason = choice.finish_reason
        if finish_reason == "tool_calls":  # <-- 判断当前返回内容是否包含 tool_calls
            messages.append(choice.message)  # <-- 我们将 Kimi 大模型返回给我们的 assistant 消息也添加到上下文中，以便于下次请求时 Kimi 大模型能理解我们的诉求
            for tool_call in choice.message.tool_calls:  # <-- tool_calls 可能是多个，因此我们使用循环逐个执行
                tool_call_name = tool_call.function.name
                tool_call_arguments = json.loads(
                    tool_call.function.arguments)  # <-- arguments 是序列化后的 JSON Object，我们需要使用 json.loads 反序列化一下
                if tool_call_name == "$web_search":
                    tool_result = search_impl(tool_call_arguments)
                else:
                    tool_result = f"Error: unable to find tool by name '{tool_call_name}'"

                # 使用函数执行结果构造一个 role=tool 的 message，以此来向模型展示工具调用的结果；
                # 注意，我们需要在 message 中提供 tool_call_id 和 name 字段，以便 Kimi 大模型
                # 能正确匹配到对应的 tool_call。
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call_name,
                    "content": json.dumps(tool_result),
                    # <-- 我们约定使用字符串格式向 Kimi 大模型提交工具调用结果，因此在这里使用 json.dumps 将执行结果序列化成字符串
                })
    try:
        total_tokens, cost = estimate_token_count(messages)
    except IndexError as e:
        print(f"Error: {e}")
        total_tokens = 0
        cost = 0
    print(choice.message.content)  # <-- 在这里，我们才将模型生成的回复返回给用户
    print(f"Total tokens: {total_tokens}, Cost: {cost}")
    return choice.message.content,cost