# ReAct Loop

ReAct: 奠定现代Agentic应用的架构，或者说算法，本质上它是利用模型的推理能力，以及tool的调用(Function Call).

模型除了能够生成自然语言的回答，还有一种特殊的生成，即生成函数调用，`function call`

![ReAct_loop.png](./attachments/ReAct_loop.png)

防御性提示词设计：降低模型幻觉的可能性

# ReAct Prompt

[01_Raw_ReAct_prompt.py](./01_Raw_ReAct_prompt.py)

不使用Function Call，利用提示词提示，让模型持续`成语接龙`。
这也是Agent ReAct最原始的一种实现思路。

- [langsmith/hwchase17/react](https://smith.langchain.com/hub/hwchase17/react)
- [langsmith/hwchase17/react-chat](https://smith.langchain.com/hub/hwchase17/react-chat)

![tool_desc.pg](./attachments/tool_desc.png)

[langsmith运行日志](https://smith.langchain.com/public/a49caa23-c18c-4289-bb6b-2c3e4ff09288/r)
程序运行结果:

可以看到如果没有符合我们的格式，直接将程序运行的错误返回给它。

![01_run_result.png](./attachments/01_run_result.png)

```sh
------------------iteration<1>----------------------
LLM Output:
Thought: 我需要先查询 laptop 的价格，然后才能应用 gold 折扣。所以我先调用 get_product_price 工具。
Action: get_product_price
Action Input: "laptop"
[Parsing] ERROR: __main__.get_product_price() argument after ** must be a mapping, not str. Try Again
------------------iteration<2>----------------------
LLM Output:
Thought: 我需要先查询 laptop 的价格。工具 get_product_price 的参数是 product，我应该提供一个 JSON 对象作为输入。
Action: get_product_price
Action Input: {"product": "laptop"}
    >>> Executing get_product_price(product='laptop')
Observation: 1299.99
------------------iteration<3>----------------------
LLM Output:
应用 gold 折扣后，一台 laptop 的价格是 974.9925。
[Parsing] ERROR: Could not parse Action/Action Input from assistant output. Try Again
------------------iteration<4>----------------------
LLM Output:
Thought: 我已经获取到 laptop 的价格为 1299.99，接下来需要调用 apply_discount 应用 gold 折扣。
Action: apply_discount
Action Input: {"price": 1299.99, "discount_tier": "gold"}
    >>> Executing apply_discount(price=1299.99,discount_tier='gold)'
Observation: 1000.99
------------------iteration<5>----------------------
LLM Output:
应用 gold 折扣后，一台 laptop 的价格是 **1000.99**。
[Parsing] ERROR: Could not parse Action/Action Input from assistant output. Try Again
------------------iteration<6>----------------------
LLM Output:
我已经得到最终答案，现在可以回答了。
Final Answer: 应用 gold 折扣后，一台 laptop 的价格是 1000.99。
  [Parsed] Final Answer: 应用 gold 折扣后，一台 laptop 的价格是 1000.99。

============================================================
Final Answer: 应用 gold 折扣后，一台 laptop 的价格是 1000.99。
------------------------------------------------------------

Thought: 我需要先查询 laptop 的价格，然后才能应用 gold 折扣。所以我先调用 get_product_price 工具。
Action: get_product_price
Action Input: "laptop"
[Parsing] ERROR: __main__.get_product_price() argument after ** must be a mapping, not str. Try Again
Thought: 我需要先查询 laptop 的价格。工具 get_product_price 的参数是 product，我应该提供一个 JSON 对象作为输入。
Action: get_product_price
Action Input: {"product": "laptop"}
Observation: 1299.99
应用 gold 折扣后，一台 laptop 的价格是 974.9925。
[Parsing] ERROR: Could not parse Action/Action Input from assistant output. Try Again
Thought: 我已经获取到 laptop 的价格为 1299.99，接下来需要调用 apply_discount 应用 gold 折扣。
Action: apply_discount
Action Input: {"price": 1299.99, "discount_tier": "gold"}
Observation: 1000.99
应用 gold 折扣后，一台 laptop 的价格是 **1000.99**。
[Parsing] ERROR: Could not parse Action/Action Input from assistant output. Try Again
------------------------------------------------------------
See you next time :)
```

# todo

居然能够打印@trace

https://wangwei1237.github.io/LLM_in_Action/
