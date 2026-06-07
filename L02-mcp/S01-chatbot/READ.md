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