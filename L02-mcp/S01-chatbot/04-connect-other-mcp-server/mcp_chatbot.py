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


    async def connect_to_servers(self):
        with open("server_config.json") as f:
            mcp_servers_config = json.load(f)
        
        servers = mcp_servers_config.get('mcpServers',{})
        for server_name,server_config in servers.items():
            print(f"connecting to {server_name}")
        

    async def connect_to_server(config: dict):
        ...
        server_params = StdioServerParameters(
            command='uv',
            args=['run', 'chatbot_mcp_server.py'],
            env=None
        )

        # Launch the server as subprocess & returns the read/write streams
        # read: the stream that client will use to read msgs from the server
        # write: the stream that client will use to write msgs to the server
        async with stdio_client(server_params) as (read, write):
            # The client session is used to initialize the connection
            # and send request to the server
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection(1:1 connection with the server)
                await session.initialize()

                # list available tools
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


async def main():
    try:
        chat_bot = McpChatBot()
        await chat_bot.connect_to_servers()
        #await self.chat_loop()
    finally:
        # clean extranel resources
        pass


if __name__ == '__main__':
    asyncio.run(main())
