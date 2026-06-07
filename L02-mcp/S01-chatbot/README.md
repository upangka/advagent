# Course Info

[Mcp Build Rich Context Ai Apps With Anthropic](https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic)


# 工具调用的基本原理

[01-function-calls](./01-function-calls)

告诉模型，该agentic应用提供了哪些工具。当模型需要调用工具的时候，会返回一条消息，要调用工具的名称和参数。

告诉模型有哪些工具tool_schema, 这里是OpenAI的格式，DeepSeek兼容这个格式，而Anthropic的格式稍微不一样。
[DeepSeek的tool_calls](https://api-docs.deepseek.com/zh-cn/guides/tool_calls)
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of a location, the user should supply a location first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"]
            },
        }
    },
]
```

模型返回的数据大概长这样:
```json
{
  "arguments": {
    "topic": "Large Language Models",
    "max_results": 10
  },
  "name":"search_pages"
}
```
接收到模型的消息之后，我们进行解析，并调用对应的工具。
一个字典，key是工具名称，value是工具函数。
```python
mapping_tool_function = {
    "search_pages": search_pages,
    "extra_info": extra_info,
}
```

调用具体的工具函数
```python
# agentic与LLM沟通的核心运转
while True:
    msg = invoke_llm(msgs)
    if msg.tool_calls:
        print(msg.content)
        # Keep the tool calls info that AI will invoke
        msgs.append(msg)

        # call the tool
        for tool in msg.tool_calls:
            result = execute_tool(tool.function.name, tool.function.arguments)
            msgs.append({"role": "tool", "tool_call_id": tool.id, "content": f"{result}"})

# 调用工具execute_tool
def execute_tool(tool: str,tool_args: str) -> str:
    kwargs = json.loads(tool_args)
    print(f'{"*"*3} 正在调用... {tool} 参数为{tool_args} {"*"*3} ')
    result = mapping_tool_function[tool](**kwargs)
    
    # ... 处理结果为字符串 ...
```

---

# MCP Server

[02-stdio-mcp-server](./02-stdio-mcp-server)
之前的工具都是在Agentic中定义，现在可以定义一个MCP Server，将工具单独放到MCP Server中。

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("mcp server name")

@mcp.tool()
def search_pages(topic: str, max_results: int = 5) -> list[str]:
    """工具描述"""
    ...
# 启动mcp server
mcp.run(transport='stdio')
```

MCP Server测试工具inspector

```shell
# uv run python chatbot_mcp_server.py
# npx @modelcontextprotocol/inspector
uv run mcp dev mcp_server_scriptxxxx.py
```
![stdio_inspect.png](assets/stdio_inspect.png)

# Agentic应用(客户端)使用MCP提供的工具

[03-mcp-client](./03-mcp-client)

核心原理两步骤：
1. 像`工具调用的基本原理`一样，首先我们需要从MCP Server中获取工具列表，绑定到模型中。
2. 当模型需要调用工具时，通过与MCP Server进行通信，将工具调用信息发送给MCP Server，MCP Server会调用对应的工具，并返回结果。
3. 将结果发回到模型中，模型会处理结果。


从MCP Server中获取工具列表，处理成模型识别的schema [DeepSeek的tool_calls](https://api-docs.deepseek.com/zh-cn/guides/tool_calls)

```python
from mcp import stdio_client, ClientSession
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # 与MCP Server建立连接
        session.initialize()
        # list available tools
        response = await session.list_tools()
        # 构建tool schema
        self.available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]
```

调用MCP Server的工具

```python
msgs = ...
msg = await self.invoke_llm(msgs)
if msg.tool_calls: # 模型需要调用工具
    # Keep the tool calls info that AI will invoke
    msgs.append(msg)
    # call the tool
    for tool in msg.tool_calls:
        # 通过session调用工具
        result = await self.session.call_tool(tool.function.name, json.loads(tool.function.arguments))
        # 回填工具结果
        msgs.append({"role": "tool", "tool_call_id": tool.id, "content": f"{result}"})
```

# 接入生态其他MCP Server

[04-connect-other-mcp-server](./04-connect-other-mcp-server)

MCP生态中提供了很多[Mcp Servers](https://github.com/modelcontextprotocol/servers)，这里提供接入方式。



这里用一个json文件进行维护[server_config.json](./04-connect-other-mcp-server/server_config.json)
这里维护的都是stido进程的启动命令，以及参数。
```json
{
  "mcpServers": {
    ...
    "research": {
      "command": "uv",
      "args": [
        "run",
        "chatbot_mcp_server.py"
      ]
    },
    "fetch": {
      "command": "uvx",
      "args": [
        "mcp-server-fetch"
      ]
    }
  }
}
```

处理配置文件
```python
with open("server_config.json") as f:
    mcp_servers_config = json.load(f)

servers = mcp_servers_config.get('mcpServers', {})
for server_name, config in servers.items():
    await self.connect_to_server(server_name, config)
```


客户端启动的时候，维护好工具与MCP Server的映射关系（因为mcp client与mcp server是`1:1`的关系）
![mcp_client_server.png](assets/mcp_client_server.png)

维护session
```python
# bind tool to session
self.tool_to_session: dict[str,ClientSession] = {}
# connect_to_server
self.tool_to_session[tool.name]=session
```

调用工具的时候，找到对应的session
```python
session = self.tool_to_session[tool_name]
result = await session.call_tool(tool_name, kwargs)
```

# Resource与Prompt

[05-resources-and-prompts](./05-resources-and-prompts)

## Resource

`@<resource>`获取客户端提供的资源，提供给模型使用。就像通义灵码(现在叫Qoder)
![tongyi_resource.png](assets/tongyi_resource.png)

只不过这里我们是通过mcp server获取的资源，但是原理是一样的

```python
@mcp.resource("papers://folders")
def get_available_folders():
    ...

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
   ...
```
这里`papers://`是资源前缀，方便客户端识别
客户端的处理的逻辑
```python
# 从mcp server获取资源uri进行维护
self.sessions: dict[str, ClientSession] = {}

# 建立连接之后进行获取资源uri与session的映射关系
resources_response = await session.list_resources()
if resources_response and resources_response.resources:
    for resource in resources_response.resources:
        rs_uri = str(resource.uri)
        self.sessions[rs_uri] = session
```
![resource_discovery.png](assets/resource_discovery.png)

---

```python
# 处理用户要获取的资源，这里以前缀来进行处理，因为topic是动态的
# 这里退化为统一前缀
async def get_resource(self, resource_uri: str):
    session = self.sessions.get(resource_uri)
    if not session and resource_uri.startswith("papers://"):
        for uri, sess in self.sessions.items():
            if uri.startswith("papers://"):
                session = sess
                break
    ...
    # 确定session直接获取资源
    response = await session.read_resource(resource_uri)
```
![resource_invocation.png](assets/resource_invocation.png)

## Prompt

MCP Server提供了prompt功能，用于生成prompt

```python
@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int) -> str:
    ...
```

客户端维护映射关系

```python
self.available_prompts: list[dict] = []

... 
# list available prompts
prompts_response = await session.list_prompts()
if prompts_response and prompts_response.prompts:
    for prompt in prompts_response.prompts:
        self.sessions[prompt.name] = session
        self.available_prompts.append({
            'name': prompt.name,
            'description': prompt.description,
            'arguments': prompt.arguments})
```
![prompt_discovery.png](assets/prompt_discovery.png)

---

获取具体的模版，需要填充参数
```python
response = await session.get_prompt(prompt_name, arguments=args)
```

![prompt_invocation.png](assets/prompt_invocation.png)


## 小结

可以发现与MCP Server的协作，无论是Resource还是Prompt，都是有两个不同的请求，可以归纳为:
1. discovery:  获取可用的资源/prompt(展示给用户)
2. invocation: 使用资源/prompt


# SSE MCP

[06-sse](./06-sse)

## Server端处理

1. 主要是创建mcp时候添加端口
2. 启动的时候指定协议transport为sse

```python
mcp = FastMCP("mcp server name xxx",port=8001)
mcp.run(transport='sse')
```

注意这里dev运行的时候要分别运行server和inspector
```sh

# 失效❌️ uv run mcp dev mcp_server_xxxx.py

# 用下面分别启动✅️
# 启动mcp server
uv run python chatbot_mcp_server.py
# 启动inspector
npx @modelcontextprotocol/inspector
```

> 服务端启动后`http://host:port/sse` 可以查看sse(sse是http的长连接，而不是websocket)

![sse.png](assets/sse.png)

## Client端处理

直接切换连接的客户端即可,使用`sse_client`来建立与mcp server的连接

```python
from mcp.client.sse import sse_client

async with sse_client("http://127.0.0.1:8001/sse") as (read, write):
    ...
```
