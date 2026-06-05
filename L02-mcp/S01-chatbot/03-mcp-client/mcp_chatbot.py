import asyncio
import json
import os
import sys

from mcp import StdioServerParameters, stdio_client, ClientSession
from openai import OpenAI


class McpChatBot:
    def __init__(self):
        self.session: ClientSession = None
        self.available_tools: list[dict] = []
        self.client = OpenAI(
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com")

    async def invoke_llm(self, messages):
        """
        Endpoint: /chat/completions
        Supported in DeepSeek.
        """
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            tools=self.available_tools,  # bind tools
            extra_body={"thinking": {"type": "disabled"}}
        )
        return response.choices[0].message

    async def process(self, query: str):
        msgs = [
            {'role': 'system', 'content': '你的名字叫AxShenZ,由"鲨鱼のJavthon"开发出来的'},
            {'role': 'user', 'content': query}]

        while True:
            msg = await self.invoke_llm(msgs)
            if msg.tool_calls:
                print(msg.content)
                # Keep the tool calls info that AI will invoke
                msgs.append(msg)

                # call the tool
                for tool in msg.tool_calls:
                    result = await self.session.call_tool(tool.function.name, json.loads(tool.function.arguments))
                    msgs.append({"role": "tool", "tool_call_id": tool.id, "content": f"{result}"})
            elif msg.content:
                print(msg.content)
                break

    async def chat_loop(self):
        print("Input query or 'quit/q' to exit")
        while (query := input("Query> ").strip().lower()) not in {'quit', 'q'}:
            await self.process(query)
            print("\n")
        else:
            print("See you next time")
            sys.exit(0)

    async def connect_to_server_and_run(self):
        server_params = StdioServerParameters(
            command='uv',
            args=['run', 'chatbot_mcp_server.py'],
            env=None
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                response = await session.list_tools()
                tools = response.tools
                print('\n Connected to server with tools: ',
                      [tool.name for tool in tools])
                self.available_tools = [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                } for tool in response.tools]

                await self.chat_loop()
                # import json
                # print(json.dumps(self.available_tools,indent=2))


async def main():
    mcp = McpChatBot()
    await mcp.connect_to_server_and_run()


if __name__ == '__main__':
    asyncio.run(main())
