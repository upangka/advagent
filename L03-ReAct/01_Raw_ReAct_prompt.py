"""Prompt engineering: the ReAct pattern
LLM justs outputs raw text,we parse it with regex
to handle tool calls and get the final answer
"""
import os

import dotenv
from openai import OpenAI
from langsmith import traceable

dotenv.load_dotenv()

model = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")


print(os.environ.get('LANGSMITH_API_KEY'))


@traceable(run_type="tool")
def hello(msg: str):
    ...


if __name__ == "__main__":
    hello("hello world")
