"""Use Function Calling to call a tool.
1. Define functions
2. Define tools schema
3. Mapping tool name to function
4. Call function according to model output
"""

import json
import os
from typing import Literal

from langsmith import traceable
from openai import OpenAI

"""
Infrastructure: Function-Tool
"""


@traceable(name="get_product_price", run_type="tool")
def get_product_price(product: str) -> float:
    """Look up the price of a product in the catalog."""
    print(f"    >>> Executing get_product_price(product={product!r})")
    catalog = {"laptop": 1299.99, "headphones": 149.95, "keyboard": 89.50}
    return catalog.get(product, 0.0)


@traceable(name="apply_discount", run_type="tool")
def apply_discount(
    price: float, discount_tier: Literal["bronze", "silver", "gold"]
) -> float:
    """Apply a discount tier to a price and return the final price.
    Args:
        price: 价格
        discount_tier: 折扣档位
    """
    print(
        f"    >>> Executing apply_discount(price={price},discount_tier='{discount_tier})'"
    )
    price = float(price)
    discounts = {"bronze": 5, "silver": 12, "gold": 23}
    discount = discounts.get(discount_tier, 0)
    return round(price * (1 - discount / 100), 2)


tools_mapping = {
    "get_product_price": get_product_price,
    "apply_discount": apply_discount,
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_product_price",
            "description": "Look up the price of a product in the catalog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "The product name to look up in the catalog.",
                    }
                },
                "required": ["product"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_discount",
            "description": "Apply a discount tier to a price and return the final price.",
            "parameters": {
                "type": "object",
                "properties": {
                    "price": {"type": "number", "description": "价格"},
                    "discount_tier": {
                        "type": "string",
                        "enum": ["bronze", "silver", "gold"],
                        "description": "折扣档位",
                    },
                },
                "required": ["price", "discount_tier"],
            },
        },
    },
]

"""
Define Model Client
"""
llm = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)


@traceable(name="DeepSeek Chat", run_type="llm")
def invoke_llm(msgs: list):
    response = llm.chat.completions.create(
        model="deepseek-v4-pro",
        messages=msgs,
        tools=tools_schema,  # type: ignore
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "disabled"}},
    )

    return response.choices[0].message


"""ReAct"""
# 防御性提示词设计:
SYSTEM_PROMPT = """
**严格规则**——你必须完全遵守以下规则：
1. 绝对不要猜测或假设任何商品价格。你必须先调用 `get_product_price` 获取真实价格。
2. 只有在通过 `get_product_price` 获取到价格之后，才能调用 `apply_discount`。传入的参数必须是 `get_product_price` 返回的精确价格——不要传入一个编造的数字。
3. 绝对不要自己用数学计算折扣。始终使用 `apply_discount` 工具。
4. 如果用户没有指定折扣档位，请询问用户使用哪个档位——不要自行假设一个。
"""

MAX_ITERATIONS = 10


def execute_tool(tool: str, tool_args: str) -> str:
    kwargs = json.loads(tool_args)
    func = tools_mapping.get(tool)
    if not func:
        raise ValueError(f"Unknown tool: {tool}")
    return str(func(**kwargs))


@traceable(name="ReAct Agent")
def run(question: str) -> str:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    msgs.append({"role": "user", "content": question})
    final_answer = ""
    for i in range(1, MAX_ITERATIONS + 1):
        print(f"------------------iteration<{i}>----------------------")
        msg = invoke_llm(msgs)
        msgs.append(msg)
        print(f"LLM Output:\n{msg.content}")
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool = tool_call.function.name
                tool_args = tool_call.function.arguments
                try:
                    tool_output = execute_tool(tool, tool_args)
                except Exception as e:
                    print(f"Error occurred while executing tool {tool}: {e}")
                    msgs.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(e),
                        }
                    )
                else:
                    msgs.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_output,
                        }
                    )
        else:
            final_answer = msg.content
            break
    else:
        print("Max iterations reached")
        return "Max iterations reached without a final answer."

    return final_answer


if __name__ == "__main__":
    question = "应用gold折扣后，一台laptop的价格是多少"
    final_answer = run(question)
    print(f"Final Answer:\n{final_answer}")
