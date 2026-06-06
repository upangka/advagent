"""
Build a MCP Server exposes two tools
"""

import json
import logging
import time

from pathlib import Path

import arxiv
from mcp.server.fastmcp import FastMCP

# 配置日志记录到文件
logging.basicConfig(
    filename='paper_research_mcp_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
PAPERS_DIR = "papers"


"""Step 01
Initialize an FastMCP Server
"""

mcp = FastMCP("research arxiv")


"""Step 02
Decorating the function with @mcp.tool().
FastMCP automatically generates the necessary MCP Schema base 
on type hints and doc-strings.
"""

@mcp.tool()
def search_pages(topic: str, max_results: int = 5) -> list[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve
    """
    # Use arxiv to find the papers
    logger.info(f"Searching for papers on arXiv based on topic: {topic}")
    client = arxiv.Client()

        # build search request
    search_req = arxiv.Search(
        query=topic,
        max_results= min(max_results,5), 
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    print(f"查询的论文数量{search_req.max_results}")
    papers = client.results(search_req)

    # store to json file
    path = Path(f"../{PAPERS_DIR}") / (topic.replace(" ", "_"))
    path.mkdir(exist_ok=True, parents=True)
    file_path = path / "papers_info.json"
    # load original paper info
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            papers_info = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
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

    with open(file_path, mode="wt", encoding="utf-8") as f:
        json.dump(papers_info, f, indent=2)
    logger.info(f"Results save in {file_path.resolve()}")
    return paper_ids

@mcp.tool()
def extra_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    Args:
        paper_id: The ID of the paper to look for
    """
    logger.info(f"Searching for information about a specific paper: {paper_id}")
    path = Path(f"../{PAPERS_DIR}")

    for item in path.iterdir():
        if item.is_dir():
            target_file = item / "papers_info.json"
            try:
                with open(target_file) as f:
                    papers_info = json.load(f)
                    if paper_id in papers_info:
                        return json.dumps(papers_info[paper_id], indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading: {target_file.resolve()} \n {e}")
    return ""


# uv run mcp dev chatbot_mcp_server.py
if __name__ == '__main__':
    logger.info(f"Starting MCP Server... at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    mcp.run(transport='stdio')
