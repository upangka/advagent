import asyncio
import json
import logging
import os
import sys

from mcp import StdioServerParameters, ClientSession
from mcp.client.sse import sse_client
from openai import OpenAI

logging.basicConfig(
    filename='mcp_client.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    encoding="utf-8"
)
logger = logging.getLogger(__name__)


class McpChatBot:
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        # Compatible with OpenAI tool schema
        self.available_tools: list[dict] = []
        self.available_prompts: list[dict] = []
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

    async def process_query(self, query: str):
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
        print("""
>>>>> MCP ChatBot start <<<<<
- Try your queries of 'quit/q' to exit.
- Use @folders to see available topic.
- Use @<topic> to search papers in that topic.
- Use /prompts to list available prompts
- Use /prompt <name> <arg1=value> to execute a prompt""")

        while (query := input("Query> ").strip().lower()) not in {'quit', 'q'}:

            # Handle prompts
            if query.startswith("/"):
                parts = query.split()
                command = parts[0]
                if command == '/prompts':
                    await self.list_prompts()
                elif command == '/prompt':
                    if len(parts) < 2:
                        print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
                        continue
                    else:
                        args = {}
                        for arg in parts[2:]:
                            if '=' in arg:
                                key, value = arg.split('=', 1)
                                args.update({key: value})
                        await self.execute_prompt(parts[1], args)
                continue
            # Handle resources
            elif query.startswith("@"):
                resource_uri = f"papers://{query[1:].lower().replace(' ', '_')}"
                await self.get_resource(resource_uri)
                continue
            # Handle query
            await self.process_query(query)
            print("\n")
        else:
            print("See you next time")
            sys.exit(0)

    async def connect_to_server_and_run(self):

        # Launch the server as subprocess & returns the read/write streams
        # read: the stream that client will use to read msgs from the server
        # write: the stream that client will use to write msgs to the server
        async with sse_client("http://127.0.0.1:8001/sse") as (read, write):
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

                for tool in response.tools:
                    self.sessions[tool.name] = session
                    self.available_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    })

                # list available prompts
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.available_prompts.append({
                            'name': prompt.name,
                            'description': prompt.description,
                            'arguments': prompt.arguments})

                # list available resources
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        rs_uri = str(resource.uri)
                        self.sessions[rs_uri] = session
                # run the chat loop
                await self.chat_loop()

    async def list_prompts(self):
        """List all available prompt"""
        if not self.available_prompts:
            print("No prompts available")
            return
        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt['arguments']:
                print(f"    Arguments")
                for arg in prompt['arguments']:
                    name = arg.name if hasattr(arg, 'name') else arg.get('name', '')
                    if name:
                        print(f"        - {name}")

    async def execute_prompt(self, prompt_name: str, args: dict):
        """
        Example:
            /prompt generate_search_prompt topic=深圳 num_papers=3
        """
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found")
            return
        try:
            response = await session.get_prompt(prompt_name, arguments=args)
            prompt_content = response.messages[0].content

            if isinstance(prompt_content, str):
                text = prompt_content
            elif hasattr(prompt_content, 'text'):
                text = prompt_content.text
            else:
                # other object to parse text...
                pass
                return
            await self.process_query(text)
        except Exception as e:
            print(f"Error executing prompt '{prompt_name}': {e.args}")

    async def get_resource(self, resource_uri: str):
        session = self.sessions.get(resource_uri)
        # handle paper resources
        if not session and resource_uri.startswith("papers://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("papers://"):
                    session = sess
                    break
        if not session:
            print(f"Resource '{resource_uri}' not found")
            return
        try:
            response = await session.read_resource(resource_uri)
            if response and response.contents:
                print(f"Resource for: {resource_uri}")
                print("Content: ")
                print(response.contents[0].text)
            else:
                print("No resources available")
        except Exception as e:
            print(f"Error reading resource '{resource_uri}': {e.args}")


async def main():
    chat_bot = McpChatBot()
    await chat_bot.connect_to_server_and_run()


if __name__ == '__main__':
    asyncio.run(main())
