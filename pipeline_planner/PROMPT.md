# FINAL MASTER PROMPT — DevTools Agentic Debugging Pipeline (Ultra-Detailed Version)

You are tasked with designing a **complete, highly optimized, multi-agent debugging pipeline** using Google’s **Agent Development Kit (ADK)**.
Your goal is to architect an “AI Debugging & System Support Team” capable of autonomously analyzing problems, investigating code, validating data, inspecting UI behavior, and producing accurate debugging conclusions — with optional admin-gated corrective actions.

---

## 1. High-Level Mission

The system should allow users — including non-developers — to describe a software issue in simple text or provide a URL, screenshot, or error message.
Your agentic pipeline must then **automatically understand the issue**, collect the required data, analyze the code and system behavior, and produce a fix or explanation.

---

## 2. Expected User Inputs

Your pipeline must handle any combination of the following:

### A. URLs

* e.g., `/login/`, `/inventory/view/123`, `/api/v1/update/`
* These may point to Django views, templates, DRF endpoints, etc.

### B. Images / Screenshots

* Django yellow error pages
* HTML screenshots
* UI rendering issues
* Console logs
* Validation errors
* Admin panel views
* Dashboard discrepancies

### C. Error Text

* Python tracebacks
* HTML error markup
* JavaScript console errors
* Custom error banners

### D. Free-Form Natural Language

* "My report isn’t showing the right numbers."
* "Clicking submit doesn’t redirect."
* "This API gives wrong data."
* "Why does this page crash?"

---

## 3. Core Objective of the Pipeline

Your job is to design a full agentic pipeline that:

1. **Understands the user’s problem.**
2. **Splits the analysis into parallel investigations** whenever possible.
3. **Reads code, data, documentation, and UI behaviors** using the available tools.
4. **Synthesizes conclusions** from all investigation threads.
5. **Explains the root cause and how to fix it.**
6. Optionally performs **safe, admin-approved corrective actions** (database fixes, documentation updates, etc.).

The system must behave like a large internal engineering team working together.

---

## 4. Tools & Systems Available to the Agents

### Knowledge Tools

* **Notion MCP (Read)** — fetch system documentation
* **Notion MCP (Write)** — update or create new documentation (**admin-gated**)
* **GitHub MCP (Read)** — fetch files, code, READMEs, docs, configuration

---

### Custom Debugging Tools

#### 1) `get_lookup_url`

* Returns:

  * URL → file path
  * URL → view function/class
  * URL → template path (if applicable)
  * URL → Django/DRF routing details

#### 2) `extract_function_source_tool`

* Given a file path and function name:

  * Returns full source code
  * Returns helper functions called inside
  * Returns docstrings and module context

#### 3) Selenium Scraper Tool / MCP Server (UI Self-Testing)

* Used to:

  * Reproduce UI flows
  * Test button clicks & form submissions
  * Inspect CSS/JS behavior
  * Capture screenshots
  * Extract HTML snippets
  * Validate page structure

This tool is **critical** for real-world debugging of UI bugs.

---

### Database Tools (GenAI Toolbox)

#### Read Access (User Level)

* Validate data
* Verify states
* Compare expected vs actual values
* Identify missing or malformed entries

#### Write Access (Admin Level)

* Fix incorrect values
* Update states
* Repair inconsistent records
* **Must always be admin-approved via a callback**

---

### ADK Built-In Tools (Use Only If Necessary)

> ADK built-in tools are **not required** to be used everywhere. They should be used **only if and where they add clear value** — not by default.

* **google_search** → Cannot be used in the initial core debugging step, but **may** be used by a sub-agent for background research or learning about unfamiliar errors or libraries.
* **EnterpriseWebSearchTool** → No active use case yet.
* **VertexAiSearchTool** → No active use case yet.
* **VertexAiRagRetrieval** → Not needed initially, but may be used in the future for fast retrieval of internal knowledge.
* **FilesRetrieval** → Useful for internal tools when system documents are fetched and need to be read.
* **url_context** → Can be useful, but many systems require login, which limits its use; may still be used for non-auth protected pages or auxiliary purposes.
* **load_memory** → **Very useful** and part of the core flow for recalling context.
* **preload_memory** → **Definitely useful** to pre-load important context before agent execution.
* **load_artifacts** → Potentially useful for loading stored artifacts (e.g., prior analysis outputs).
* **exit_loop** → Useful and likely needed in Loop Agents for controlled termination.
* **get_user_choice** → **Critical** for gathering extra clarification and for **admin approval** before performing sensitive actions.
* **LongRunningFunctionTool** → **Very useful** for time-consuming operations such as deep code scanning, DB analysis, or multi-file searches.

The same principle applies to **callbacks** — they should only be used where they add real value (logging, security, enrichment, approvals), not everywhere by default.

---

## 5. System Design Requirements

You must design:

### A. A Complete Multi-Layered Agentic Architecture

* This must **not** be a single-agent solution.
* It must be a **hierarchical, multi-stage pipeline**.

### B. Use All Agent Types Where Appropriate — Multiple Times

You are free to decide **where** and **how often** to use:

* **Sequential agents** (can and should be used multiple times).
* **Parallel agents** (can and should be used multiple times).
* **Loop agents** (can and should be used multiple times).
* **LlmAgents** wherever natural language reasoning, tool orchestration, or synthesis is needed.

You must decide the best places to use each type based on efficiency, clarity, and robustness.

### C. The Pipeline Should Mimic a Real Engineering Team

* Triage / intake
* Classification of the problem
* Parallel investigation tracks
* Deep code analysis
* Data validation and DB checks
* UI/UX reproduction (for web systems)
* Documentation lookup and comparison
* Iterative refinement where needed
* Synthesis of findings
* Final resolution / explanation
* Optional admin-gated actions (DB write, documentation updates, etc.)

### D. Requirements for the Investigation Stage

This is the heart of the system. It must support:

* **Code Path Identification**

  * URL → file/function/class → template → routing details.

* **Function & Sub-function Reading**

  * Understand what the function does, what helpers it calls, what models it touches, etc.

* **Logic Understanding**

  * Infer control flow, branching, validation logic, and error conditions.

* **Data Relevance & DB Validation**

  * When appropriate, check database state to see if the data contributes to or explains the bug.

* **User-Flow & UI Reproduction (Web Systems)**

  * Use the Selenium tool to reproduce steps, test interactions, and capture live behavior.

* **Documentation Comparison**

  * Compare actual behavior against intended/expected behavior from docs (Notion or other knowledge sources).

This stage should:

* Run **parallel analyses** where possible.
* Use **loops** for iterative refinement or multiple attempts.
* Use **sequencing** to structure multi-step reasoning.

---

## 6. Example Scenario (For Understanding)

User uploads a screenshot of a Django yellow error page and says:

> "This page is crashing when I try to submit a form."

Your pipeline should be capable of:

1. Extracting the URL (from screenshot or text if available).
2. Identifying the Django view / function / template involved.
3. Reading the function code and relevant helpers.
4. Checking whether specific input data values in the DB affect this behavior.
5. Using Selenium to reproduce the UI flow and confirm the failure.
6. Combining insights from code, data, UI, and docs.
7. Explaining the **root cause** and **how to fix it** (in clear language).
8. Optionally proposing or performing **safe admin-gated updates** (e.g., fixing a bad config or correcting data).

---

## 7. Final Output Expectations

Your result must include:

* A fully detailed, coherent **system architecture**.
* A **multi-layered agentic pipeline** with clear stages.
* Clear descriptions of how each stage behaves and what it is responsible for.
* The flow of data and context between agents.
* When and how tools are invoked (decided by the agents).
* Where sequencing, parallelism, or loops are most beneficial.
* How edge cases and ambiguities are handled.
* How admin approvals are implemented (e.g., via `get_user_choice`).
* How memory and artifacts are used to carry context across steps.
* How the final answer to the user is synthesized and presented.

You are free to design the pipeline and choose the best structure.

---

## 8. Final Instruction

**Generate the absolute best, most efficient, deeply detailed, logical, expandable, production-ready agentic debugging pipeline architecture based on EVERYTHING above — using multiple Sequential, Parallel, Loop, and LLM agents wherever appropriate.**

You have full freedom to design the optimal system.
