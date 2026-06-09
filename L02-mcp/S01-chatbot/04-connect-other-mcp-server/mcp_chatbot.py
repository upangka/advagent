import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, stdio_client
from openai import OpenAI


class McpChatBot:
    def __init__(self):
        self.sessions: list[ClientSession] = []
        self.available_tools: list[dict] = []
        self.exit_stack = AsyncExitStack()
        self.client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
        # bind tool to session
        self.tool_to_session: dict[str, ClientSession] = {}

    async def invoke_llm(self, messages):
        """
        Endpoint: /chat/completions
        Supported in DeepSeek.
        """
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            tools=self.available_tools,  # bind tools
            extra_body={"thinking": {"type": "disabled"}},
        )
        return response.choices[0].message

    async def process(self, query: str):
        msgs = [
            {
                "role": "system",
                "content": '你的名字叫AxShenZ,由"鲨鱼のJavthon"开发出来的',
            },
            {"role": "user", "content": query},
        ]

        while True:
            msg = await self.invoke_llm(msgs)
            if msg.tool_calls:
                print(msg.content)
                # Keep the tool calls info that AI will invoke
                msgs.append(msg)

                # call the tool
                for tool in msg.tool_calls:
                    tool_name = tool.function.name
                    kwargs = json.loads(tool.function.arguments)
                    print(f"Calling tool: {tool_name} with args: {kwargs}")

                    session = self.tool_to_session[tool_name]
                    result = await session.call_tool(tool_name, kwargs)
                    msgs.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool.id,
                            "content": f"{result}",
                        }
                    )
            elif msg.content:
                print(msg.content)
                break

    async def chat_loop(self):
        print("Input query or 'quit/q' to exit")
        while (query := input("Query> ").strip().lower()) not in {"quit", "q"}:
            await self.process(query)
            print("\n")
        else:
            print("See you next time")
            sys.exit(0)

    async def connect_to_servers(self):
        """Connect to all configured MCP Servers

        Prepare MCP server-related tools
        """

        with open("server_config.json") as f:
            mcp_servers_config = json.load(f)

        servers = mcp_servers_config.get("mcpServers", {})
        for server_name, config in servers.items():
            await self.connect_to_server(server_name, config)

        with open("tools_schema.json", mode="wt", encoding="utf-8") as f:
            json.dump(self.available_tools, f, indent=2)

        print(f"The agent has a total of {len(self.available_tools)} tools\n")
        print(
            "    ".join(
                [
                    f'({id}):{tool["function"]["name"]}'
                    for id, tool in enumerate(self.available_tools, 1)
                ]
            )
        )

    async def connect_to_server(self, name: str, config: dict):

        server_params = StdioServerParameters(**config)

        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        self.sessions.append(session)

        # Initialize the connection(1:1 connect with the server)
        await session.initialize()

        # list available tools
        response = await session.list_tools()
        tools = response.tools
        print(
            f"\n Connected to {name} server with tools: ", [tool.name for tool in tools]
        )

        for tool in response.tools:
            # Prepared MCP server-related tools
            self.tool_to_session[tool.name] = session
            self.available_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
            )

    async def cleanup(self):
        """Clean up all resources"""
        await self.exit_stack.aclose()


async def main():
    try:
        chat_bot = McpChatBot()
        await chat_bot.connect_to_servers()
        await chat_bot.chat_loop()
    finally:
        # clean external resources
        await chat_bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
