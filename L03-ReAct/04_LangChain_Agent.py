"""
LangChain Agent
"""

from typing import Literal

import dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langsmith import traceable

from helper import SYSTEM_PROMPT

dotenv.load_dotenv()
llm = init_chat_model(
    "deepseek:deepseek-v4-pro",
    temperature=0.8,
    extra_body={"thinking": {"type": "disabled"}},
)


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


# Agent = Model +
agent = create_agent(
    model=llm, tools=[get_product_price,
                      apply_discount], system_prompt=SYSTEM_PROMPT
)


@traceable()
def run_agent(question: str):
    """Run the agent with the given input."""
    print(f"    >>> Running agent with question: {question}")

    # 高度封装的ReAct直接得到结果
    # type(agent_result) is dict
    agent_result = agent.invoke(
        input={"messages": [{"role": "user", "content": question}]}
    )
    return agent_result["messages"][-1].content_blocks


if __name__ == "__main__":
    answer = run_agent("应用gold折扣后，一台laptop的价格是多少")
    print("———" * 30)
    print(f"answer = {answer[0]["text"]}")
    print("———" * 30)
