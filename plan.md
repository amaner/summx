
# SummX Development Plan

This document outlines a **dependency-aware** development plan for SummX.

We now assume:

- SummX uses a **forked local copy** of **Emi’s Arxiv-MCP server** as its arXiv backend.
- The MCP layer (`McpSession`, `ArxivMcpClient`) talks to this server via MCP.
- We will **generalize** Emi’s SE-focused defaults (e.g., `cs.SE`) where needed.

The high-level strategy:

1. Build **stable foundations** (models, config, LLM abstraction).
2. Implement and test the **agent pipeline** with mocks.
3. Integrate **MCP + Emi’s server fork**.
4. Layer on **CLI** and **UI**.
5. Harden with tests, real integration, and documentation.

---

## Phase 0 — Repo Skeleton & Environment

**Goal:** Have a clean, runnable Python package skeleton with no real logic yet.

### Tasks

- [ ] Create basic repo structure:
  - `pyproject.toml`
  - `README.md`
  - `plan.md`
  - `src/summx/` plus subpackages:
    - `models/`, `llm/`, `mcp/`, `agent/`, `cli/`, `ui/`
- [ ] Add minimal `__init__.py` files so everything imports.
- [ ] Set up environment (conda or venv) and install dependencies:
  ```bash
  pip install -e .
  pip install -e ".[dev]"
  ```

**Exit criteria**

* `python -c "import summx"` succeeds.
* `pytest` runs (even if there are no tests yet).

---

## Phase 1 — Domain Models & Config

**Goal:** Define core data structures and configuration that everything else depends on.

### 1.1 Models

**Files**

* `src/summx/models/paper.py`
* `src/summx/models/plan.py`
* `src/summx/models/__init__.py`

**Tasks**

* [ ] Implement paper-related models:

  * `PaperMeta`
  * `PaperContentSections`
  * `PaperSummary`
  * `PaperResult`
* [ ] Implement planning models:

  * `SummarizationConfig`
  * `SearchFilters`
  * `SearchPlan`
* [ ] Add unit tests:

  * `tests/test_models.py` — construct and validate these dataclasses.

**Exit criteria**

* `from summx.models import PaperMeta, SearchPlan` works.
* Basic model tests pass.

### 1.2 Config

**File**

* `src/summx/config.py`

**Tasks**

* [ ] Implement `SummXConfig` or simple helpers to:

  * Load env vars:

    * API keys (OpenAI, Groq, etc.)
    * MCP command (`MCP_ARXIV_COMMAND`)
    * MCP args (`MCP_ARXIV_ARGS`)
    * MCP storage path (`MCP_ARXIV_STORAGE_PATH`)
  * Define default models:

    * Planner provider/model
    * Summarizer provider/model
* [ ] Implement `load_config()` returning a config object.

**Exit criteria**

* `from summx.config import load_config` works.
* Config can be created without hitting external services.

---

## Phase 2 — LLM Abstraction Layer

**Goal:** Have a unified way to talk to LLM providers (OpenAI, Groq) that the agent can use.

### Files

* `src/summx/llm/base.py`
* `src/summx/llm/openai_client.py`
* `src/summx/llm/groq_client.py`
* `src/summx/llm/__init__.py`

### Tasks

* [ ] Define `LLMClient` abstract base with:

  * `async def chat(self, messages: list[dict[str, str]]) -> str`
* [ ] Implement `OpenAIClient`:

  * Wrap OpenAI chat completions.
* [ ] Implement `GroqClient`:

  * Wrap Groq chat completions.
* [ ] Implement `get_llm(provider, api_key, model)` factory.
* [ ] Implement a `DummyLLMClient` (for tests) that returns canned responses.

**Exit criteria**

* A simple test can create a `DummyLLMClient` and call `.chat()` successfully.
* LLM factory tests pass.

---

## Phase 3 — Prompts & Planner (Agent Part 1)

**Goal:** Convert natural-language queries into structured `SearchPlan` objects.

### Files

* `src/summx/prompts.py`
* `src/summx/agent/planner.py`

### Tasks

* [ ] Implement `QUERY_PLANNER_SYSTEM` and any helper templates in `prompts.py`:

  * Ensure the planner emits **JSON-only** responses.
* [ ] Implement `QueryPlanner`:

  * Holds a planner `LLMClient`.
  * `async plan(raw_query: str) -> SearchPlan`.
* [ ] Use `DummyLLMClient` for tests:

  * Provide a fixed JSON response.
  * Confirm correct parsing into `SearchPlan`.

**Exit criteria**

* `QueryPlanner.plan()` returns a valid `SearchPlan` for a mocked LLM.
* Planner module tests pass.

---

## Phase 4 — Fork & Configure Emi’s Arxiv-MCP Server

**Goal:** Prepare a local, forked MCP server instance that SummX can talk to.

> This phase is new/specific to the Emi choice.

### External Repo (outside `summx/`)

* [ ] Fork Emi’s Arxiv-MCP repo into your GitHub.
* [ ] Clone your fork locally.

### Tasks in the fork

* [ ] Set up local environment following Emi’s instructions (preferably with `uv`).
* [ ] Identify the `search_papers` implementation and:

  * Change **default category** from `cs.SE` to:

    * Something more general (e.g. `None`, or a configurable default).
* [ ] Optionally neutralize SE-specific phrasing in tool descriptions.
* [ ] Add a minimal config file or env var support if needed for:

  * default categories,
  * rate limiting,
  * storage path.

### Integration tasks in SummX

* [ ] Decide on `MCP_ARXIV_COMMAND` / `MCP_ARXIV_ARGS`, e.g.:

  * `MCP_ARXIV_COMMAND="uv"`
  * `MCP_ARXIV_ARGS="tool run arxiv-mcp --storage-path ~/.summx/papers"`
* [ ] Add these fields to `SummXConfig`.

**Exit criteria**

* You can start the forked Arxiv-MCP server locally from the command line.
* It responds correctly to `search_papers` for **non-SE categories** when invoked directly (e.g. via a test client or CLI).

---

## Phase 5 — MCP Session & Arxiv Client

**Goal:** Wrap Emi’s MCP server with a stable Python interface.

### Files

* `src/summx/mcp/session.py`
* `src/summx/mcp/arxiv_client.py`
* `src/summx/mcp/__init__.py`

### 5.1 MCP Session

**Tasks**

* [ ] Implement `McpSession`:

  * Uses `SummXConfig` to spawn the forked Arxiv-MCP server.
  * Provides `call_tool(name: str, arguments: dict) -> dict`.
  * Handles process lifecycle (`start()`, `stop()`, or context manager).

For now, **mock** `call_tool` in unit tests; full integration comes later.

### 5.2 Arxiv Client

**Tasks**

* [ ] Implement `ArxivMcpClient` methods:

  * `search_papers(topic, author, sort, limit, category=None) -> list[PaperMeta]`

    * Build tool payload and call `session.call_tool("search_papers", {...})`.
    * Map Emi’s response format → `PaperMeta`.
  * `download_paper(arxiv_id) -> str | None`
  * `read_paper(arxiv_id) -> PaperContentSections`
* [ ] Ensure `search_papers` always passes a `category` argument:

  * At minimum, allow `None` to mean “no category filter.”
  * Later, use planner to pick categories based on topic.

### 5.3 Tests

* [ ] Use mocked `McpSession.call_tool` to simulate Emi’s tool outputs.
* [ ] Unit-test mapping of JSON → `PaperMeta` / `PaperContentSections`.

**Exit criteria**

* `ArxivMcpClient.search_papers()` and `read_paper()` work with mocked MCP responses.
* No direct dependency on Emi’s actual server in unit tests (that’s for integration tests later).

---

## Phase 6 — Executor & PaperAgent (Agent Part 2)

**Goal:** Execute `SearchPlan` using ArxivMcpClient + summarizer LLM to produce `PaperResult` list.

### Files

* `src/summx/agent/executor.py`
* `src/summx/agent/__init__.py`

### Tasks

#### 6.1 PlanExecutor

* [ ] Implement `PlanExecutor`:

  * Holds `ArxivMcpClient` and summarizer `LLMClient`.
  * `async execute(plan: SearchPlan) -> list[PaperResult]`:

    * Calls `search_papers()` using `plan.filters`, `plan.sort`, `plan.limit`.
    * For each paper:

      * If `plan.summarization.enabled`:

        * Call `read_paper(arxiv_id)` → `PaperContentSections`.
        * Build summarization prompt (from `prompts.py`).
        * Call summarizer LLM → `PaperSummary`.
      * Build `PaperResult`.

#### 6.2 PaperAgent

* [ ] Implement `PaperAgent`:

  * Holds `QueryPlanner` + `PlanExecutor`.
  * `async run(raw_query: str) -> tuple[SearchPlan, list[PaperResult]]`.

### Tests

* [ ] Mock `ArxivMcpClient` and summarizer `LLMClient`:

  * Confirm `execute()` correctly assembles `PaperResult` objects.
* [ ] Integration-style test:

  * `PaperAgent.run()` with dummy planner/executor wiring.

**Exit criteria**

* Agent pipeline works end-to-end in tests using mocks only.

---

## Phase 7 — CLI

**Goal:** Provide a practical `summx` CLI that wraps `PaperAgent`.

### Files

* `src/summx/cli/main.py`
* `src/summx/cli/__init__.py`
* `tests/test_cli.py`

### Tasks

* [ ] Implement Typer app (`app = typer.Typer()`).
* [ ] Implement `summx query`:

  * Accepts a natural-language query.
  * Loads config.
  * Constructs:

    * planner LLM
    * summarizer LLM
    * `McpSession` + `ArxivMcpClient`
    * `QueryPlanner`, `PlanExecutor`, `PaperAgent`
  * Calls `await PaperAgent.run(query)`.
  * Prints plan + results (titles, authors, PDF links, maybe short TL;DR).
* [ ] Implement `summx ui`:

  * Launches Streamlit app, e.g.:

    ```bash
    streamlit run summx/ui/streamlit_app.py
    ```

### Tests

* [ ] Use Typer’s `CliRunner` with a mocked `PaperAgent`:

  * Ensure commands parse arguments and call agent correctly.

**Exit criteria**

* `summx --help` shows both `query` and `ui` commands.
* `summx query "..."` runs with mocked components in tests.

---

## Phase 8 — Streamlit UI

**Goal:** Build a simple web UI for non-CLI users.

### Files

* `src/summx/ui/streamlit_app.py`
* `src/summx/ui/__init__.py`

### Tasks

* [ ] Set up basic Streamlit layout:

  * Page title, wide layout.
* [ ] Sidebar:

  * Planner provider/model selection.
  * Summarizer provider/model selection.
  * Summarization depth.
  * Limit (# of papers).
* [ ] Main area:

  * Query text input.
  * “Run agent” button.
  * Display interpreted `SearchPlan`.
  * Display a card per `PaperResult`:

    * Title, authors, date, categories.
    * Download link (arXiv PDF URL or local cached PDF).
    * Markdown summary.

**Exit criteria**

* `summx ui` opens the SummX UI in a browser.
* Running a query shows at least mocked/dummy results (initially).

---

## Phase 9 — Real Integration with Emi’s MCP Server

**Goal:** Wire SummX to the real forked Arxiv-MCP server and test end-to-end.

### Tasks

* [ ] Confirm `McpSession` can start/stop the forked server using `MCP_ARXIV_COMMAND`/`ARGS`.

* [ ] Add integration tests (optional, may be marked/slow) that:

  * Spin up a real `McpSession` (or run against an already running server).
  * Call `ArxivMcpClient.search_papers()` with real categories (e.g. `math.CO`).
  * Confirm results map into `PaperMeta`.

* [ ] Manually test:

  * CLI queries:

    * `summx query "five most recent papers on hyper graphs"`
    * `summx query "most recent publication by <author>"`
  * UI queries with the same.

* [ ] Ensure category handling works:

  * No hidden `cs.SE` bias survives from Emi’s defaults.
  * Planner → Plan → ArxivMcpClient flow supports arbitrary categories.

**Exit criteria**

* SummX can fetch real arXiv papers via Emi’s server.
* Summaries are generated end-to-end for real queries.

---

## Phase 10 — Polishing, Docs, and DX

**Goal:** Make SummX usable and understandable for other researchers.

### Tasks

* [ ] Update `README.md`:

  * Installation (conda/venv, how to install your Emi fork).
  * MCP backend explanation.
  * Usage: CLI + UI.
  * Architecture overview (link to UML sections).
* [ ] Document category behavior clearly:

  * How SummX avoids being SE-only.
  * How to tweak category handling in config or planner.
* [ ] Add docstrings to public classes/methods.
* [ ] (Optional) Add `docs/` or mkdocs site.
* [ ] Add Jupyter notebook examples:

  * Programmatic usage:

    ```python
    from summx.agent import PaperAgent
    ```

**Exit criteria**

* A new researcher can:

  * Clone SummX and your Arxiv-MCP fork.
  * Follow README instructions.
  * Run `summx query` and `summx ui` on their own machine.
  * Understand enough architecture to extend or debug.

---

## Short Summary of Implementation Order

1. **Models + Config**
2. **LLM abstraction + DummyLLM**
3. **Prompts + QueryPlanner**
4. **Fork Emi’s Arxiv-MCP + adjust defaults**
5. **McpSession + ArxivMcpClient (mocked tests)**
6. **PlanExecutor + PaperAgent (mocked tests)**
7. **CLI (`summx query`, `summx ui`)**
8. **Streamlit UI**
9. **Real integration with forked Emi MCP server**
10. **Polish, docs, and ergonomics**

This ordering reflects the fact that we now **depend on a customizable MCP backend** (Emi’s server) but still want to keep SummX loosely coupled and testable with mocks independently of that backend.
