"""
LLM call tools

implement the two tools
"""

import os
import json

import arxiv
from openai import OpenAI


# define two function tools
def search_pages(topic: str, max_results: int = 5) -> list[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve
    """
    # Use arxiv to find the papers
    client = arxiv.Client()

    # build search request
    search_req = arxiv.Search(
                query=topic,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
    papers = client.results(search_req)
    print(list(papers))




def extra_info(paper_id: str):
    """
    Search for information about a specific paper across all topic directories.
    Args:
        paper_id: The ID of the paper to look for
    """
    ...


# define tool mapping
mapping_tool_function = {
    "search_pages": search_pages,
    "extra_info": extra_info,
}

# define tool schema pass to llm
tool_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_pages",
            "description": "Search for papers on arXiv based on a topic and store their information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to search for",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to retrieve",
                        "default": 5
                    }
                },
                "required": ["topic"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extra_info",
            "description": "Search for information about a specific paper across all topic directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paper_id": {
                        "type": "string",
                        "description": "The ID of the paper to look for",
                    }
                },
                "required": ["paper_id"]
            },
        }
    }
]


# define function to invoke the LLM

def invoke_llm(messages):
    """
    Endpoint: /chat/completions
    Supported in DeepSeek.
    """
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
        tools=tool_schema,  # bind tools
        extra_body={"thinking": {"type": "disabled"}}
    )
    return response.choices[0].message


# using the new OpenAI API https://developers.openai.com/api/docs/guides/function-calling
def invoke_llm_with_new_api(messages):
    """error in deepseek
    end point: /responses
    Not support in deepseek
    """
    response = client.responses.create(
        model="deepseek-v4-pro",
        input=messages
    )
    return response


client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

msgs = [{'role': 'user', 'content': '你能使用工具?'}]
#response = invoke_llm(msgs)
#print(response.model_dump_json(indent=2))
