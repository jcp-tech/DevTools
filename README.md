# Developer Support System — Plan&#x20;

> **Note:** Built on **ADK (Agent Development Kit)**, focused on debugging a **Django + MySQL system**.

## 1) Purpose

Help users debug issues by providing details (screenshots, Django yellow error pages, HTML, images, or free‑form descriptions). The AI agent will understand the problem and follow a standard, step‑by‑step debugging procedure, delegating tasks to sub‑agents/tools as needed.

## 2) Scope (Current)

* **Agentic Framework:** ADK (core orchestration layer)
* **Target Framework for Debugging:** Django
* **Database:** MySQL
* **Context Inputs:**

  * Screenshots
  * Yellow error page text (raw HTML, image, or plain text)
  * Free‑form problem details
  * Links/URLs inside the app (when available)

## 3) Debugging Workflow (Existing)

1. **If a link is provided:**

   * Extract file/function location from the link.
2. **If file or function path is known:**

   * Read the function docstring (`__doc__`) first, then the full function code.
   * If sub‑functions are referenced inside, read them too and understand their behavior.
   * Use this to reconstruct the logic of the function for deeper understanding.
3. **Use database models when relevant:**

   * Understand what data enters the function and where it goes.
4. **Understand the data flow:**

   * Rely on any available documentation (acknowledging it may be limited).

## 4) Tools (Existing)

* **ADK as Orchestration Layer**

  * Hosts the agent network; coordinates sub‑agents and tool calls.
* **GenAI Toolkit Toolbox**

  * Connect to **MySQL** (initially **read‑only**; later, controlled write access will be enabled after verification).
* **Custom‑Built Tool (to be converted to ADK’s MCP Server)**

  * Lists the different links in the system.
  * Given a link for debugging, returns key details (URL, file path, name, etc.) with schema guaranteed for locating the code.
* **File/Function Reading Tools**

  * Via **GitHub MCP** and/or a **custom code‑parsing tool** (both may be used; GitHub MCP is ideal but limited on alternate branches).

## 5) Assumptions & Constraints (As Stated)

* System documentation exists but is limited.
* The agent should prioritize understanding function logic and data flow from real code and models.
* MySQL: start with **read‑only access**. Controlled writes added later once reliability is proven.
* The ADK agent network is separate from Django, with only database + tool permissions for debugging.
* Links inspector guarantees correct schema for locating code.

## 6) Supporting Context (New)

* **Notion Documentation** will be provided, containing scenarios, problems, and mitigation strategies. This gives the agent context on system logic and expected flows.
* **Agentic Pipelines in ADK:** ADK will orchestrate multiple specialized agents working together in a pipeline.
* **Audit Trail (Future To‑Do):** Logging every debugging step is **very important**, but will be added after the system stabilizes.

## 7) Current Status Summary

* Planning a multi‑agent debugging flow using ADK as the orchestration framework.
* Flow starts from user-provided artifacts (links, error pages, screenshots, text) and drills into code, sub‑functions, and models to map data flow and logic.
* Tooling to resolve links → code locations and to read code is in scope.
* MySQL connectivity via GenAI toolkit is in scope (read‑only first).
* Notion docs and audit trail are part of the future roadmap.

<!-- <iframe src="https://www.linkedin.com/embed/feed/update/urn:li:share:7368415904369405952?collapsed=1" height="598" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe> -->