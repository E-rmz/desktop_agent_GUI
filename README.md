

````markdown
# 🧠 desktop_agent_GUI

This project provides tools for automating desktop browser interactions using LLM-based agents, with integrations via LangGraph and Microsoft's Playwright MCP server.

---

## 🛠 Installation and Setup

It is recommended to install all dependencies using the **[uv](https://docs.astral.sh/uv/)** package manager:

```bash
uv venv
uv add <your packages>
````

### 🔐 Environment Variables

Create a `.env` file in the root of your project and add the following keys:

```env
GOOGLE_API_KEY="your-api-key"
GOOGLE_MODEL=gemini-2.0-flash
PLAYWRIGHT_HEADLESS=false
```

---

## 📁 Project Files Overview

This project includes two main files that form the core of the desktop automation agent:

### `main.py`

This script connects to the **Playwright MCP server** built by Microsoft and acts as a client that communicates with the server to perform browser automation tasks.(**It connects to MCP server but Not Working Properly. i will back to it later**

### `playwright_direct_agent.py`

This script integrates Playwright tools directly into a **reAct-style agent** pattern built using **LangGraph**.
Although still a work in progress, it is functional and can accept natural language commands such as:

> "Open xyz.com website, then go to abc.net, stay there for 10 seconds, and close the tab."

The script will interpret and execute these browser actions step-by-step.

---

## 📌 Notes

* Tested on macOS (Apple Silicon).

