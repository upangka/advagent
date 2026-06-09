"""
Using LangChain Abstractions to build a ReAct Loop

Here, only the LangChain abstractions for tools, messages, and model clients are used.
"""

from configparser import MAX_INTERPOLATION_DEPTH
from typing import Literal

import dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langsmith import traceable

# enable tracing with LangSmith
dotenv.load_dotenv()

MAX_INTERRATIONS = 10


@tool
def get_product_price(product: str) -> float:
    """Look up the price of a product in the catalog."""
    print(f"    >>> Executing get_product_price(product={product!r})")
    catalog = {"laptop": 1299.99, "headphones": 149.95, "keyboard": 89.50}
    return catalog.get(product, 0.0)


@tool
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


llm = init_chat_model(
    "deepseek:deepseek-v4-pro",
    temperature=0.2,
    extra_body={"thinking": {"type": "disabled"}},
)

tools = [get_product_price, apply_discount]
tools_mapping = {tool.name: tool for tool in tools}

#  Bind tools: under the hood, automatically generate tool schemas for the model.
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """
你是一个商品客户助手，你能够使用工具来更好的服务客户。
**严格规则**——你必须完全遵守以下规则：
1. 绝对不要猜测或假设任何商品价格。你必须先调用 `get_product_price` 获取真实价格。
2. 只有在通过 `get_product_price` 获取到价格之后，才能调用 `apply_discount`。传入的参数必须是 `get_product_price` 返回的精确价格——不要传入一个编造的数字。
3. 绝对不要自己用数学计算折扣。始终使用 `apply_discount` 工具。
4. 如果用户没有指定折扣档位，请询问用户使用哪个档位——不要自行假设一个。
"""


@traceable(name="LangChain Abc Agent Loop")
def run(question: str) -> str:
    msgs = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]

    for i in range(1, MAX_INTERRATIONS + 1):
        print(f"------------------iteration<{i}>----------------------")
        msg = llm_with_tools.invoke(msgs)
        print(f"LLM Output:\n{msg.content}")
        msgs.append(msg)
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                # type(tool_call) is dict
                tool_call_id = tool_call["id"]
                toolname = tool_call["name"]
                toolargs = tool_call.get("args", {})
                tool = tools_mapping[toolname]
                if not tool:
                    print(f"    >>> Tool {toolname} not found")
                    # Should use HumanMessage or ToolMessage to feed this info back to the model???
                    # Yes: should use ToolMessage!!!
                    msgs.append(
                        ToolMessage(
                            content=f"[Error] Tool {toolname} not found. Try Again",
                            tool_call_id=tool_call_id,
                        )
                    )
                    continue
                try:
                    # Note: use invoke() instead of __call__()
                    observation = tool.invoke(toolargs)
                    msgs.append(
                        ToolMessage(content=str(observation), tool_call_id=tool_call_id)
                    )
                except Exception as e:
                    print(f"    >>> Error occurred while executing {toolname}: {e}")
                    msgs.append(
                        ToolMessage(
                            content=f"[Error] Failed to execute {toolname}: {e}. Try Again",
                            tool_call_id=tool_call_id,
                        )
                    )
        else:
            return msg.content

    return "Max iterations reached."


if __name__ == "__main__":
    final_answer = run("应用gold折扣后，一台laptop的价格是多少")
    print("——" * 30)
    print(f"Final Answer:\n{final_answer}")
    print("——" * 30)
