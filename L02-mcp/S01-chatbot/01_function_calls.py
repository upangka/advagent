"""
bind only tools in application
"""
import os
from openai import OpenAI


# define two function tools
def search_pages(topic: str, max_results: int = 5) -> list[str]:
    ...


def extra_info(paper_id: str):
    ...


# define tool mapping
mapping_tool_function = {
    "search_pages": search_pages,
    "extra_info": extra_info,
}

# define tool schema pass to llm
tool_schema = ...


# define invoke llm

def invoke_llm(messages):
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        mesasges=messages,
        tools=tool_schema
    )
    return response.choices[0].message

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")