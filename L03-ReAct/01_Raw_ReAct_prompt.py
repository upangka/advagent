"""Prompt engineering: the ReAct pattern
LLM justs outputs raw text,we parse it with regex
to handle tool calls and get the final answer
"""
import os
from typing import Literal
import dotenv
from openai import OpenAI
from langsmith import traceable
import inspect
dotenv.load_dotenv()

model = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")


@traceable(run_type="tool")
def get_product_price(product: str) -> float:
    """Look up the price of a product in the catalog."""
    print(f"    >>> Executing get_product_price(product='{product}')")
    catalog = {"laptop": 1299.99, "headphones": 149.95, "keyboard": 89.50}
    return catalog.get(product, 0.0)


@traceable(run_type="tool")
def apply_discount(price: float, discount_tier: Literal['bronze', 'silver', 'gold']) -> float:
    """Apply a discount tier to a price and return the final price."""
    print(f"    >>> Executing apply_discount(price={price},discount_tier='{discount_tier})'")
    price = float(price)
    discounts = {
        'bronze': 5,
        'silver': 12,
        'gold': 23
    }
    discount = discounts.get(discount_tier, 0)
    return round(price * (1 - discount / 100), 2)


def get_tool_descriptions(tools: dict) -> str:
    """Handle all tools to text descriptions"""
    desc = []
    
    for name,f in tools.items():
        signature = inspect.signature(f.__wrapped__)
        docstring = inspect.getdoc(f)
        desc.append(f"{name}{signature} - {docstring}")

    return "\n".join(desc)


tools = {
    "get_product_price": get_product_price,
    "apply_discount": apply_discount
}

tool_descriptions = get_tool_descriptions(tools)
tool_name = ", ".join(tools.keys())

# https://smith.langchain.com/hub/hwchase17/react
# 防御性提示词设计: 防止模型幻觉

react_prompt = f"""
请尽你所能回答以下问题。你可以使用以下工具: 

{tool_descriptions}

请使用以下格式: 

Question: 你需要回答的输入问题
Thought: 你应该始终思考下一步要做什么
Action: 要执行的动作，应为 [{tool_name}] 之一
Action Input: 该动作的输入内容
Observation: 动作执行的结果
...（这个 Thought/Action/Action Input/Observation 可以重复 N 次）
Thought: 我现在知道最终答案了
Final Answer: 对原始输入问题的最终答案

开始！

Question: {{question}}
Thought: """


if __name__ == "__main__":
    ...
