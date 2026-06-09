"""
Build a MCP Server expose resource and prompt
1. resource: like http get method
"""

import json
import logging
import time
from pathlib import Path

import arxiv
from mcp.server.fastmcp import FastMCP

# 配置日志记录到文件
logging.basicConfig(
    filename="mcp_server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

PAPERS_DIR = "papers"
PAPER_FILE_NAME = "papers_info.json"

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
def search_papers(topic: str, max_results: int = 5) -> list[str]:
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
        max_results=min(max_results, 5),
        sort_by=arxiv.SortCriterion.Relevance,
    )

    print(f"查询的论文数量{search_req.max_results}")
    papers = client.results(search_req)

    # store to json file
    path = Path(f"../{PAPERS_DIR}") / (topic.lower().replace(" ", "_"))
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
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
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


@mcp.resource("papers://folders")
def get_available_folders():
    """
    List all available topic folders in the papers directory.
    This resource provides a simple list of all available topic folders
    """
    logger.info("Receive request for get_available_folds")
    path = Path(f"../{PAPERS_DIR}")

    folds = []
    for topic in path.iterdir():
        target = topic / "papers_info.json"
        if target.exists():
            folds.append(topic.name)

    content = "# Available Topic\n\n"

    # Create a simple markdown list
    if folds:
        for idx, folder in enumerate(folds, 1):
            content += f"{idx}. {folder}\n"
        content += f"\nUse @{folder} to access papers in that topic.\n"  # noqa: F823
    else:
        content += "No topics found.\n"

    return content


@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Get detail information about papers on topic

    Args:
        topic: The research topic to retrieve papers for

    """
    logger.info(f"Receive request for get_topic_papers to get {topic}")

    topic_dir = topic.lower().replace(" ", "_")
    papers_file = Path(f"../{PAPERS_DIR}") / f"{topic_dir}/{PAPER_FILE_NAME}"

    if not papers_file.exists():
        print(papers_file.resolve())
        return f"No papers found for that topic: {topic}.\n\nTry searching for papers on another topic"

    try:
        with open(papers_file, mode="rt", encoding="utf-8") as f:
            papers = json.load(f)

        # Create markdown content with paper detail
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers)}\n\n"

        for idx, paper in papers.items():
            content += f"## {paper['title']}\n"
            content += f"- **Paper ID**: {idx}\n"
            content += f"- **Authors**: {', '.join(paper['authors'])}\n"
            content += f"- **Published**: {paper['published']}\n"
            content += f"- **PDF URL**: [{paper['pdf_url']}]({paper['pdf_url']})\n\n"
            content += f"> **Summary**\n> {paper['summary'][:500]}...\n\n"
            content += f"---\n\n"

        # save result markdown
        outdir = Path(f"../out")
        outdir.mkdir(exist_ok=True)
        with open(outdir / f"{topic_dir}.md", mode="wt", encoding="utf-8") as f:
            f.write(content)
        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."


@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int) -> str:
    """Generate a prompt for Hosts to find and discuss academic papers on a specific topic."""

    return f"""使用 search_papers 工具搜索关于 '{topic}' 的 {num_papers} 篇学术论文。请按照以下指示操作：
    1. 首先，使用 search_papers(topic='{topic}', max_results={num_papers}) 搜索论文。
    
    2. 对于找到的每一篇论文，提取并整理以下信息：
       - 论文标题
       - 作者
       - 发表日期
       - 关键发现简述
       - 主要贡献或创新点
       - 使用的方法论
       - 与主题 '{topic}' 的相关性
    
    3. 提供一份综合总结，内容包括：
       - '{topic}' 领域的研究现状概述
       - 多篇论文中出现的共同主题和趋势
       - 关键的研究空白或未来研究方向
       - 该领域中最具影响力或最重要的论文
    
    4. 将你的发现以清晰、结构化的格式呈现，使用标题和要点，便于阅读。
    
    请同时提供每篇论文的详细信息，以及对 {topic} 研究领域的高层次综合概述。"""


# uv run mcp dev chatbot_mcp_server.py
if __name__ == "__main__":
    logger.info(
        f"Starting MCP Server... at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
    )
    mcp.run(transport="stdio")
