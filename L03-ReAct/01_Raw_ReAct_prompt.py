"""Prompt engineering: the ReAct pattern
LLM justs outputs raw text,we parse it with regex
to handle tool calls and get the final answer
"""

from collections import namedtuple
from typing import Literal, Optional, Tuple, Any, NamedTuple

import inspect
import json
import os
import re
from typing import Literal, Optional, Tuple, Any

import dotenv
from langsmith import traceable
from openai import OpenAI

dotenv.load_dotenv()

MAX_ITERATIONS = 5

llm = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)


@traceable(name="DeepSeek Chat", run_type="llm")
def invoke_llm(full_prompt: str):
    response = llm.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "user", "content": full_prompt},
        ],
        stop="\nObservation",  # Stop World
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}},
    )

    return response.choices[0].message


@traceable(run_type="tool")
def get_product_price(product: str) -> float:
    """Look up the price of a product in the catalog."""
    print(f"    >>> Executing get_product_price(product={product!r})")
    catalog = {"laptop": 1299.99, "headphones": 149.95, "keyboard": 89.50}
    return catalog.get(product, 0.0)


@traceable(run_type="tool")
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


def get_tool_descriptions(tools: dict) -> str:
    """Handle all tools to text descriptions"""
    desc = []

    for name, f in tools.items():
        signature = inspect.signature(f.__wrapped__)
        docstring = inspect.getdoc(f)
        desc.append(f"{name}{signature} - {docstring}")

    return "\n".join(desc)


def parse_final_answer(content: str) -> Optional[str]:
    """Extract final answer from LLM response content."""
    final_answer_match = re.search(r"Final Answer:\s*(.+)", content)
    if final_answer_match:
        return final_answer_match.group(1).strip()
    return None


def parse_action_and_input(content: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract action and action input from LLM response content."""
    action_match = re.search(r"Action:\s*(.+)", content)
    action_input_match = re.search(r"Action Input:\s*(.+)", content)

    action = action_match.group(1).strip() if action_match else None
    action_input = action_input_match.group(
        1).strip() if action_input_match else None

    return action, action_input


class ToolExecuteResult(NamedTuple):
    result: Any
    error: Optional[str]


def execute_tool(tool_name: str, tool_args_str: str, tools: dict) -> ToolExecuteResult:
    """
    Execute a tool with given arguments.
    Returns ToolExecuteResult with result and error_message (None if successful).
    """
    tool = tools.get(tool_name)
    if not tool:
        return ToolExecuteResult(None, f"[Parsing] ERROR: Tool '{tool_name}' not found. Try Again")

    try:
        args = json.loads(tool_args_str)
    except json.JSONDecodeError:
        return ToolExecuteResult(None, f"[Parsing] ERROR: Action Input is not valid JSON. Try Again")

    try:
        result = tool(**args)
        return ToolExecuteResult(result, None)
    except Exception as e:
        return ToolExecuteResult(None, f"[Parsing] ERROR: {e}. Try Again")


@traceable(name="ReAct Loop backup DeepSeek")
def run(question: str):
    prompt = react_prompt.format(question=question)
    scratchpad = ""
    final_answer = "Not Found"

    for i in range(1, MAX_ITERATIONS + 1):
        print(f"------------------iteration<{i}>----------------------")
        full_prompt = prompt + scratchpad + "\nThought: "
        msg = invoke_llm(full_prompt)
        content = msg.content.strip() if msg.content else ""  # type: ignore

        print(f"LLM Output:\n{content}")

        # Check for final answer
        final_answer = parse_final_answer(content)
        if final_answer:
            print(f"  [Parsed] Final Answer: {final_answer}")
            print("\n" + "=" * 60)
            print(f"Final Answer: {final_answer}")
            break

        # Parse action and action input
        toolname, toolargs = parse_action_and_input(content)
        if not toolname or not toolargs:
            error = "[Parsing] ERROR: Could not parse Action/Action Input from assistant output. Try Again"
            print(error)
            scratchpad += f"\n{msg.content}\n{error}" if msg.content else f"\n{error}"
            continue

        # Execute tool
        tool_result = execute_tool(toolname, toolargs, tools)
        if tool_result.error:
            print(tool_result.error)
            scratchpad += f"\n{msg.content}\n{tool_result.error}" if msg.content else f"\n{tool_result.error}"
            continue

        # Handle successful tool execution
        observation = f"Observation: {tool_result.result}"
        print(observation)
        scratchpad += f"\n{msg.content}\n{observation}" if msg.content else f"\n{observation}"
    else:
        print("Max iterations reached. Exiting.")
        return "Max iterations reached. Exiting."

    print("--"*30)
    print(scratchpad)
    print("--"*30)
    return final_answer


tools = {"get_product_price": get_product_price,
         "apply_discount": apply_discount}

tool_descriptions = get_tool_descriptions(tools)
tool_name = ", ".join(tools.keys())

# https://smith.langchain.com/hub/hwchase17/react
# 防御性提示词设计: 防止模型幻觉

react_prompt = f"""
**严格规则**——你必须完全遵守以下规则：
1. 绝对不要猜测或假设任何商品价格。你必须先调用 `get_product_price` 获取真实价格。
2. 只有在通过 `get_product_price` 获取到价格之后，才能调用 `apply_discount`。传入的参数必须是 `get_product_price` 返回的精确价格——不要传入一个编造的数字。
3. 绝对不要自己用数学计算折扣。始终使用 `apply_discount` 工具。
4. 如果用户没有指定折扣档位，请询问用户使用哪个档位——不要自行假设一个。
5. Action Input: 该动作的输入内容必须是json字符串的形式

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
"""


if __name__ == "__main__":
    run("应用gold折扣后，一台laptop的价格是多少")
