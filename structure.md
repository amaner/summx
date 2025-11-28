---
js:
  - https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js
---

This file - **`structure.md`** -focuses purely on **architecture, structure, and UML** instead of installation/marketing.

This reflects the **API-first design, MCP as optional**, and the complete module layout with class diagrams.

---

# SummX — Architecture & Structure

This document describes the **internal architecture, module structure, and class design**
for SummX.

Unlike a user README, this file is meant for **developers and contributors** who want to
understand, extend, or re-implement parts of the system.

---

## 1. High-Level Architecture

SummX is an **agentic research assistant** built around the following pipeline:

```text
User Query
↓
QueryPlanner (LLM)
↓
SearchPlan
↓
PaperAgent
↓
PlanExecutor
↓
PaperSourceClient  ───────────→ arXiv
↓                          (via API or MCP)
Results + Summaries
↓
CLI / UI
```

The system is layered to allow **backend swapping** and **LLM/provider abstraction**.

---

## 2. Key Design Principle

The most important design decision:

> The agent does **not** depend directly on MCP or the arXiv API.
> It only depends on a generic `PaperSourceClient` interface.

This means:

- Current production backend: ✅ `ArxivApiClient`
- Optional future backend: `ArxivMcpClient` (using a forked MCP server)

---

## 3. Global UML Overview

```mermaid
classDiagram
    class SummXCLI
    class SummXUI

    class PaperAgent {
        +run(query) → (SearchPlan, List[PaperResult])
    }

    class QueryPlanner {
        +plan(query) → SearchPlan
        -llm: LLMClient
    }

    class PlanExecutor {
        +execute(plan) → List[PaperResult]
        -sourceClient: PaperSourceClient
        -llm: LLMClient
    }

    class PaperSourceClient {
        <<abstract>>
        +search_papers(plan)
        +read_paper(arxiv_id)
        +get_pdf_url(arxiv_id)
    }

    class ArxivApiClient
    class ArxivMcpClient

    class LLMClient {
        <<abstract>>
        +chat(messages)
    }

    SummXCLI --> PaperAgent
    SummXUI --> PaperAgent

    PaperAgent --> QueryPlanner
    PaperAgent --> PlanExecutor

    QueryPlanner --> LLMClient
    PlanExecutor --> PaperSourceClient
    PlanExecutor --> LLMClient

    PaperSourceClient <|-- ArxivApiClient
    PaperSourceClient <|-- ArxivMcpClient
```

---

## 4. Module & Directory Structure

```text
src/summx/
├── __init__.py
├── config.py
├── prompts.py
│
├── models/
│   ├── __init__.py
│   ├── paper.py
│   └── plan.py
│
├── llm/
│   ├── __init__.py
│   ├── base.py
│   ├── openai_client.py
│   └── groq_client.py
│
├── sources/
│   ├── __init__.py
│   ├── base.py
│   └── arxiv_api_client.py
│
├── agent/
│   ├── __init__.py
│   ├── planner.py
│   ├── executor.py
│   └── agent.py
│
├── cli/
│   ├── __init__.py
│   └── main.py
│
├── ui/
│   ├── __init__.py
│   └── streamlit_app.py
│
└── mcp/              (optional / experimental)
    ├── __init__.py
    ├── session.py
    └── arxiv_mcp_client.py
```

---

## 5. Models Layer (`models/`)

### Purpose

Defines all domain objects used throughout the system.

### UML

```mermaid
classDiagram
    class PaperMeta {
        +arxiv_id: str
        +title: str
        +authors: List[str]
        +categories: List[str]
        +published: str
        +abstract: str
        +pdf_url: str
        +local_pdf_path: Optional[str]
    }

    class PaperContentSections {
        +abstract: str
        +introduction: Optional[str]
        +methods: Optional[str]
        +results: Optional[str]
        +conclusion: Optional[str]
        +full_text: Optional[str]
        +other_sections: dict
    }

    class PaperSummary {
        +short_summary: str
        +long_summary: str
        +key_points: List[str]
    }

    class PaperResult {
        +meta: PaperMeta
        +content: Optional[PaperContentSections]
        +summary: Optional[PaperSummary]
        +plan_tags: List[str]
    }

    class SearchFilters {
        +topic: Optional[str]
        +author: Optional[str]
        +categories: List[str]
        +date_from: Optional[str]
        +date_to: Optional[str]
    }

    class SummarizationConfig {
        +enabled: bool
        +depth: str
        +max_tokens: int
    }

    class SearchPlan {
        +filters: SearchFilters
        +limit: int
        +sort: str
        +summarization: SummarizationConfig
    }

    PaperResult --> PaperMeta
    PaperResult --> PaperContentSections
    PaperResult --> PaperSummary
    SearchPlan --> SearchFilters
    SearchPlan --> SummarizationConfig
```

---

## 6. LLM Layer (`llm/`)

### Purpose

Abstracts away provider differences between OpenAI, Groq, etc.

### UML

```mermaid
classDiagram
    class LLMClient {
        <<abstract>>
        +chat(messages: List[dict]) → str
    }

    class OpenAIClient {
        -api_key: str
        -model: str
    }

    class GroqClient {
        -api_key: str
        -model: str
    }

    class DummyLLMClient

    LLMClient <|-- OpenAIClient
    LLMClient <|-- GroqClient
    LLMClient <|-- DummyLLMClient
```

---

## 7. Source Layer (`sources/`)

### Purpose

Provides a backend-independent abstraction over paper sources.

### Structure

```text
sources/
├── base.py             # PaperSourceClient
└── arxiv_api_client.py # ArxivApiClient (primary backend)
```

### UML

```mermaid
classDiagram
    class PaperSourceClient {
        <<abstract>>
        +search_papers(plan)
        +read_paper(arxiv_id)
        +get_pdf_url(arxiv_id)
    }

    class ArxivApiClient {
        +search_papers(plan)
        +read_paper(arxiv_id)
    }

    class ArxivMcpClient {
        +search_papers(plan)
        +read_paper(arxiv_id)
        +session: McpSession
    }

    PaperSourceClient <|-- ArxivApiClient
    PaperSourceClient <|-- ArxivMcpClient
```

---

## 8. Agent Layer (`agent/`)

### Purpose

Encapsulates the agentic reasoning flow.

### UML

```mermaid
classDiagram
    class QueryPlanner {
        -llm: LLMClient
        +plan(query) → SearchPlan
    }

    class PlanExecutor {
        -source: PaperSourceClient
        -llm: LLMClient
        +execute(plan) → List[PaperResult]
    }

    class PaperAgent {
        -planner: QueryPlanner
        -executor: PlanExecutor
        +run(query) → (SearchPlan, List[PaperResult])
    }

    PaperAgent --> QueryPlanner
    PaperAgent --> PlanExecutor
    PlanExecutor --> PaperSourceClient
    QueryPlanner --> LLMClient
```

---

## 9. CLI Layer (`cli/`)

Implemented using Typer.

Responsibilities:

* Parse user input.
* Construct core objects.
* Run the agent.
* Render summaries & metadata to terminal.

### UML

```mermaid
classDiagram
    class SummXCLI {
        +query(text)
        +ui()
    }

    SummXCLI --> PaperAgent
```

---

## 10. UI Layer (`ui/`)

Implemented using Streamlit.

Responsibilities:

* Input box for user queries.
* Display structured paper cards.
* Provide PDF download links.

### UML

```mermaid
classDiagram
    class StreamlitApp {
        +main()
        -build_agent()
        -render_results()
        -render_paper_card()
    }

    StreamlitApp --> PaperAgent
    StreamlitApp --> PaperResult
```

---

## 11. Optional MCP Layer (`mcp/`)

This layer is **not currently required** and is considered experimental.

It exists to allow SummX to talk to a forked MCP arXiv server.

### UML

```mermaid
classDiagram
    class McpSession {
        +call_tool(name, args)
        +start()
        +stop()
    }

    class ArxivMcpClient {
        -session: McpSession
        +search_papers(plan)
        +read_paper(arxiv_id)
    }

    ArxivMcpClient --> McpSession
```

---

## 12. Final Architectural Summary

* The **agent/core logic is complete and MCP-independent**.
* MCP exists as a **replaceable backend**, not a blocking dependency.
* The system is:

  * Modular
  * Testable
  * Pluggable
  * Designed for long-term research workflows.

This architecture supports:

* Adding more sources (e.g. PubMed, semantic scholar).
* Adding more LLM providers.
* Introducing multi-agent research later.

---

## End

This file intentionally avoids installation, usage, or marketing —
those belong in a separate `README.md`.

This file exists only to define how SummX is structured, how modules
interact, and how it should evolve.

