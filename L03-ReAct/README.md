# ReAct Loop

ReAct: 奠定现代Agentic应用的架构，或者说算法，本质上它是利用模型的推理能力，以及tool的调用(Function Call).

模型除了能够生成自然语言的回答，还有一种特殊的生成，即生成函数调用，`function call`

![ReAct_loop.png](./attachments/ReAct_loop.png)

防御性提示词设计：降低模型幻觉的可能性

# ReAct Prompt

不使用Function Call，利用提示词提示，让模型持续`成语接龙`。
这也是Agent ReAct最原始的一种实现思路。

- [langsmith/hwchase17/react](https://smith.langchain.com/hub/hwchase17/react)
- [langsmith/hwchase17/react-chat](https://smith.langchain.com/hub/hwchase17/react-chat)

# todo

居然能够打印@trace
