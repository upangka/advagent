"""
A chatbot that retrieves papers from arXiv based on the topic the user inputs.
LLM call tools
implement the two tools
"""

import sys
import os
import json
from pathlib import Path
import arxiv
from openai import OpenAI

PAPERS_DIR="papers"


"""Step 01
define tool functions ,tool schema, tool mapping
"""

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
    
    # store to json file
    path = Path(f"../{PAPERS_DIR}") / (topic.replace(" ","_"))
    path.mkdir(exist_ok=True,parents=True)
    file_path = path / "papers_info.json"
    # load original paper info
    try:
        with open(file_path,mode="r",encoding="utf-8") as f:
            papers_info = json.load(f)
    except (FileNotFoundError,json.JSONDecodeError):
        print("init papers_info to empty {}")
        papers_info = {}

    paper_ids = []
    
    for paper in papers:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper_id] = paper_info
    
    with open(file_path,mode="wt",encoding="utf-8") as f:
        json.dump(papers_info,f,indent=2)
    print(f"Results save in {file_path.resolve()}")
    return paper_ids



def extra_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    Args:
        paper_id: The ID of the paper to look for
    """
    path = Path(f"../{PAPERS_DIR}")

    for item in path.iterdir():
        if item.is_dir():
            target_file = item / "papers_info.json"
            try:
                with open(target_file) as f:
                    papers_info = json.load(f)
                    if paper_id in papers_info:
                        return json.dumps(papers_info[paper_id],indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading: {target_file.resolve()} \n {e}")
    return ""

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

"""Step 02
define how to invoke llm
"""

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

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

"""Step 03 
Define the chatbot
"""

def parse():
    ...

# Chat Loop
def chat_loop():
    print("Input queries topic or 'quit/q' to exit")
    while (topic := input("Query> ").strip().lower()) not in {'quit','q'}:
          ...
    else:
        print("See you next time")
        sys.exit(0) 

chat_loop()











