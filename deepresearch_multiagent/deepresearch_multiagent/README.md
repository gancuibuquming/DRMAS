# DeepResearch Multi-Agent System

一个可直接运行的 **DeepResearch 多 Agent 研究系统**。项目重点是：多 Agent 分工、状态流转、SSE 实时输出、检查点恢复、可替换 LLM/Search 接口，以及最终带引用的研究报告生成。

> 默认不强依赖真实 API：没有 `OPENAI_API_KEY` / `TAVILY_API_KEY` 时会自动使用 Mock 模式，方便你先跑通流程；接入真实 key 后即可换成真实 LLM 和搜索。

---

## 1. 系统架构

```text
用户问题
  │
  ▼
PlannerAgent       研究计划拆解：生成 research questions / search queries
  │
  ▼
SearchAgent        联网检索/本地模拟检索：返回带 URL 的候选来源
  │
  ▼
ReaderAgent        阅读与摘取证据：抽取关键事实、观点、引用片段
  │
  ▼
AnalystAgent       综合分析：归纳主题、冲突信息、证据强弱
  │
  ▼
CriticAgent        可信度审查：检查缺口、幻觉风险、引用覆盖
  │
  ▼
WriterAgent        生成最终报告：结构化输出 + Sources
```

核心能力：

- **6 个 Agent 分工协作**：Planner / Searcher / Reader / Analyst / Critic / Writer。
- **SSE 流式输出**：前端/调用方可以实时看到每个 Agent 的阶段性结果。
- **Checkpoint 恢复**：每一步会保存到 `data/checkpoints/{session_id}.json`。
- **可插拔 LLM**：默认 Mock，可切换到 OpenAI。
- **可插拔 Search**：默认 Mock，可切换到 Tavily 或 SerpAPI。
- **可扩展工具层**：保留 tools 目录，便于加入知识库检索、Text2SQL、网页抓取等。

---

## 2. 快速启动

```bash
cd deepresearch_multiagent
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

没有 key 也可以运行，系统会自动使用 Mock 模式。

如需真实 OpenAI：

```env
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4.1-mini
```

如需真实搜索，推荐 Tavily：

```env
TAVILY_API_KEY=tvly-xxx
```

---

## 3. API 使用

### 创建研究任务

```bash
curl -X POST http://127.0.0.1:8000/api/research/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "RAG 系统中如何降低幻觉并提升答案可追溯性？",
    "depth": "standard",
    "language": "zh"
  }'
```

### 读取 SSE 流

```bash
curl -N http://127.0.0.1:8000/api/research/sessions/<session_id>/stream
```

### CLI 运行

```bash
python -m app.cli "RAG 系统中如何降低幻觉并提升答案可追溯性？" --depth standard --language zh
```

---

## 4. 目录结构

```text
deepresearch_multiagent/
├── app/
│   ├── main.py                  FastAPI 入口
│   ├── cli.py                   命令行入口
│   ├── core/
│   │   ├── config.py            配置
│   │   ├── events.py            SSE 事件结构
│   │   ├── llm.py               LLM 适配层
│   │   └── logging.py           日志
│   ├── models/
│   │   └── schemas.py           API Schema
│   ├── research/
│   │   ├── graph.py             Agent 编排图
│   │   ├── state.py             研究状态对象
│   │   ├── checkpoint.py        检查点保存/恢复
│   │   └── agents/
│   │       ├── base.py
│   │       ├── planner.py
│   │       ├── searcher.py
│   │       ├── reader.py
│   │       ├── analyst.py
│   │       ├── critic.py
│   │       └── writer.py
│   └── tools/
│       ├── search.py            搜索工具
│       └── web_reader.py        网页读取工具占位
├── static/
│   └── index.html               简易调试前端
├── data/
│   └── checkpoints/             运行时生成
├── tests/
│   └── test_smoke.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 5. 二次开发建议

### 接入你自己的知识库/RAG

在 `app/tools/search.py` 中新增一个 `KnowledgeBaseSearchProvider`，返回统一的 `Source`：

```python
Source(
    title="文档标题",
    url="kb://doc-id#chunk-3",
    snippet="召回片段",
    source="knowledge_base",
    score=0.91,
)
```

然后在 `SearchAgent` 里把 web search 和 knowledge search 做 RRF 融合即可。

### 增加 Agent

新增文件：

```text
app/research/agents/new_agent.py
```

继承 `BaseAgent`，然后在 `app/research/graph.py` 的 `self.agents` 里加入即可。

### 接入 LangGraph

当前版本为了方便运行，使用纯 Python 编排。你可以把 `ResearchGraph` 替换为 LangGraph 的 `StateGraph`，但建议先保留本项目的状态结构和 checkpoint 逻辑。

---

## 6. 简历表达

- 设计 Planner/Searcher/Reader/Analyst/Critic/Writer 六 Agent 协作链路，实现复杂研究任务的自动拆解、检索、证据抽取与报告生成。
- 基于 SSE 推送 Agent 中间状态，支持前端实时展示研究进度，并通过 JSON checkpoint 实现任务中断恢复。
- 抽象 LLM/Search Provider 接口，支持 Mock、本地知识库、Tavily/OpenAI 等多种后端平滑切换。
