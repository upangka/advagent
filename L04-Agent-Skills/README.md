skills-compatible AI application

`Skill` = 结构化的`Prompt`体系 + 配套资源文件 + 渐进式加载机制

`Skill` 让 `Agent`(如Claude） 的"大脑"里同时装着几十个专家，每个专家只在自己被需要时才"醒来"——这叫 `"专家池"模式`。

Agent Skills 是一种轻量级、开放格式的 AI 代理能力扩展方案。(Agent Skills are a lightweight open format for extending AI agent capabilities)

| 方案                   | 重量级                                  | 轻量级 |
| ---------------------- | --------------------------------------- | ------ |
| 微调模型 (Fine-tuning) | 需要GPU、数据集、训练流程，成本数万美金 | ❌     |
| RAG（检索增强生成）    | 需要向量数据库、Embedding模型、维护索引 | ❌     |
| MCP Server             | 需要独立服务进程、网络通信、复杂配置    | ❌     |
| Agent Skill            | 只需要一个文件夹 + 一个Markdown文件     | ✅     |

A **skill** is a **folder of organized files** consisting of instructions,scripts,assets and resources that agents can discover to perform a specific task accurately.

```txt
┌─────────────────────────────────────────────────────────────┐
│                    Skill = 文件夹                           │
├─────────────────────────────────────────────────────────────┤
│  📄 SKILL.md          ← 必需：核心指令（"怎么做"）          │
│  📁 scripts/          ← 可选：可执行代码（"动手做"）        │
│  📁 assets/           ← 可选：静态素材（"用什么工具"）      │
│  📁 references/       ← 可选：参考资料（"按什么标准"）      │
│  📁 templates/        ← 可选：输出模板（"长什么样"）        │
├─────────────────────────────────────────────────────────────┤
│  发现机制：Agent 启动时扫描 → 按任务匹配 → 按需加载         │
└─────────────────────────────────────────────────────────────┘
```

![](./images/skills.png)
![](./images/scripts.png)
![](./images/assets.png)

# Resource

[Deeplearn.ai: agent-skills-with-anthropic](https://learn.deeplearning.ai/courses/agent-skills-with-anthropic/lesson/ldn5c3/introduction)

[Bilibi: agent-skills-with-anthropic](https://www.bilibili.com/video/BV1qv6eBZErD/?spm_id_from=333.337.search-card.all.click&vd_source=f9745f81b4981bb1eca8c2d80be33ff9)

[Github Repo](https://github.com/https-deeplearning-ai/sc-agent-skills-files/tree/main)
