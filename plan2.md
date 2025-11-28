
Below is a **fully rewritten `plan.md`** that:

* Treats MCP as **optional / future work**
* Makes the **direct arXiv API backend** the primary integration
* Keeps your architecture modular so MCP can be plugged back in later without rewrites
* Reflects where you *actually* are now (CLI issues, need for stability)

You can drop this straight into your repo as `plan.md`.

---

# SummX Development Plan (Revised)

This plan reflects a strategic pivot away from **MCP as a hard dependency** and toward a **direct arXiv API–based backend** first, with MCP remaining an optional
advanced integration later.

Key philosophy:

> Get the core pipeline (planner → agent → executor → CLI/UI) fully stable before
> depending on under-documented external components.

---

## High-Level Architecture (Updated)

Instead of hard-coding MCP, SummX now uses a pluggable **Paper Source Interface**:

```text
QueryPlanner → SearchPlan → PaperAgent → PlanExecutor → PaperSourceClient → arXiv
│
├── ArxivApiClient ✅ (Primary)
└── McpArxivClient   (Optional / later)
```

This ensures:
- Your CLI/UI work regardless of MCP availability.
- MCP can be reintroduced later without breaking your agent pipeline.

---

## Phase 0 — Repo Skeleton & Environment

**Goal:** Clean Python package with working imports & test harness.

### Tasks
- [x] Define project structure under `src/summx/`
- [x] Create:
  - `README.md`
  - `plan.md`
  - `pyproject.toml`
- [x] Setup environment (`conda` or `venv` + pip).
- [x] Ensure:
  ```bash
  python -c "import summx"
  pytest
  ```

**Exit Criteria**

* Package imports cleanly.
* Tests run (even if empty).

---

## Phase 1 — Domain Models & Config

**Goal:** Define stable domain objects for papers, plans, and results.

### Files

* `src/summx/models/paper.py`
* `src/summx/models/plan.py`
* `src/summx/models/__init__.py`
* `src/summx/config.py`

### Tasks

* [ ] Implement paper models:

  * `PaperMeta`
  * `PaperContentSections`
  * `PaperSummary`
  * `PaperResult`
* [ ] Implement planning models:

  * `SearchFilters`
  * `SummarizationConfig`
  * `SearchPlan`
* [x] Implement `SummXConfig`:

  * LLM options
  * Default source client type
  * API keys
  * Optional MCP config

### Exit Criteria

* Models can be imported and instantiated.
* Unit tests validate dataclass behavior.

---

## Phase 2 — LLM Abstraction Layer

**Goal:** Unified LLM interface for OpenAI, Groq, etc.

### Files

* `src/summx/llm/base.py`
* `src/summx/llm/openai_client.py`
* `src/summx/llm/groq_client.py`
* `src/summx/llm/__init__.py`

### Tasks

* [x] Define `LLMClient` base class.
* [x] Implement:

  * `OpenAIClient`
  * `GroqClient`
  * `DummyLLMClient` (for tests)
* [x] Implement `get_llm()` factory.
* [x] Test with mock prompts.

### Exit Criteria

* You can call `.chat(...)` on any provider.
* Unit tests use `DummyLLMClient`.

---

## Phase 3 — Planner Layer

**Goal:** Convert natural language into structured plans.

### Files

* `src/summx/prompts.py`
* `src/summx/agent/planner.py`

### Tasks

* [x] Define planner prompt for emitting strict JSON.
* [x] Implement `QueryPlanner.plan(raw_query) → SearchPlan`.
* [x] Write tests using `DummyLLMClient`.

### Exit Criteria

* Planner converts input like:

  > “Show most recent hypergraph papers”
  > into a valid `SearchPlan`.

---

## Phase 4 — Paper Source Abstraction

**Goal:** Remove MCP dependency from core logic.

### Files

* `src/summx/sources/base.py`
* `src/summx/sources/arxiv_api_client.py`

### Tasks

#### 4.1 Source Interface

Implement generic paper source base class:

```python
class PaperSourceClient:
    async def search_papers(self, plan: SearchPlan) -> list[PaperMeta]:
        ...
    async def read_paper(self, arxiv_id: str) -> PaperContentSections:
        ...
    async def get_pdf_url(self, arxiv_id: str) -> str:
        ...
```

#### 4.2 Primary Backend — arXiv API

Implement `ArxivApiClient` using the `arxiv` Python package:

* [x] Implement `search_papers`
* [x] Implement `read_paper` (metadata + abstract first)
* [x] Generate PDF URLs
* [x] Unit test mapping into SummX models

### Exit Criteria

* Can search arXiv directly without MCP.
* Returns valid `PaperMeta` and `PaperContentSections`.

---

## Phase 5 — Executor + PaperAgent

**Goal:** End-to-end agent logic with no CLI yet.

### Files

* `src/summx/agent/executor.py`
* `src/summx/agent/agent.py`

### Tasks

* [x] Implement `PlanExecutor` using `PaperSourceClient`.
* [x] Implement `PaperAgent` using:

  * `QueryPlanner`
  * `PlanExecutor`
* [x] Unit test agent pipeline using:

  * `ArxivApiClient`
  * `DummyLLMClient`

### Exit Criteria

* Calling:

  ```python
  plan, results = await agent.run("Recent hypergraph papers")
  ```

  returns structured, summarized results.

---

## Phase 6 — CLI Interface

**Goal:** Fully functional terminal interface.

### Files

* `src/summx/cli/main.py`

### Tasks

* [ ] Implement `summx query "..."`
* [ ] Wire to:

  * `QueryPlanner`
  * `PaperAgent`
  * `ArxivApiClient`
* [ ] Format output:

  * Titles
  * Authors
  * PDF links
  * Summaries
* [ ] Add `summx ui` launcher.

### Exit Criteria

* You can run:

  ```bash
  summx query "5 most recent hypergraph papers"
  ```

without MCP and get real results.

---

## Phase 7 — Streamlit UI

**Goal:** GUI interface for exploration.

### Files

* `src/summx/ui/streamlit_app.py`

### Tasks

* [ ] Query input
* [ ] Model/provider selection
* [ ] Display cards for each paper
* [ ] PDF download links
* [ ] Summary rendered via markdown

### Exit Criteria

* `summx ui` launches web UI.
* Queries display paper lists + summaries.

---

## Phase 8 — Optional: MCP Reintegration (Deferred)

**Goal:** Add MCP as an optional backend, not a dependency.

### Files

* `src/summx/mcp/session.py`
* `src/summx/mcp/arxiv_mcp_client.py`

### Tasks

* [ ] Implement `McpArxivClient(PaperSourceClient)`
* [ ] Translate MCP tool responses → SummX models.
* [ ] Add config flag:

  ```bash
  SUMMX_SOURCE=mcp
  ```
* [ ] Only use MCP if explicitly enabled.

### Exit Criteria

* SummX works in two modes:

  * `SUMMX_SOURCE=api` ✅
  * `SUMMX_SOURCE=mcp` (experimental)

---

## Phase 9 — Polish & Documentation

**Goal:** Make it usable by other researchers.

### Tasks

* [ ] Update README to reflect:

  * API-first design
  * Optional MCP backend
* [ ] Add quick-start guide.
* [ ] Add example queries.
* [ ] Add warning that MCP backend is experimental.

---

## Final Execution Order

```
Models & Config
   ↓
LLM Layer
   ↓
Planner
   ↓
Paper Source Interface
   ↓
ArxivApiClient ✅
   ↓
Executor + Agent
   ↓
CLI ✅
   ↓
UI ✅
   ↓
(MCP optional)
```

---

## Strategic Outcome

This plan ensures:

✅ You get a working SummX CLI *now*
✅ UI builds on stable foundations
✅ MCP doesn’t block core development
✅ You retain future extensibility

---

If you want, next I can help you rewrite your README’s architecture section to reflect this new “API-first with MCP optional” design.
