# 🚀 Fuse - The AI-Native Automation Engine

[![PyPI version](https://badge.fury.io/py/fuse-io.svg)](https://badge.fury.io/py/fuse-io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Fuse** is a powerful **local-first** workflow automation platform designed from the ground up for the agentic era. Build complex, intelligent automations with a beautiful visual builder, modular node system, and deep AI integration.

> **"Bridging the gap between AI capabilities and real-world processes."** ⚡

---

## 🌟 Why Fuse?

Unlike traditional automation tools, Fuse is built with an **AI-first** philosophy. It doesn't just "support" AI; it treats LLMs and Agents as first-class citizens of your workflow ecosystem.

- **🔒 Local-First & Privacy-Centric**: Run your workflows locally. Your data, your rules.
- **🤖 Agentic Orchestration**: Native support for autonomous AI Agents that can plan, execute, and iterate.
- **🔌 Infinite Extensibility**: A modular architecture where every node and plugin is an isolated, versioned package.
- **🌌 Antigravity Support**: Dynamic proxying to unlock pro-tier models (Claude 3.5/4.5, Gemini Pro) via local entitlements.

---

## ✨ Features

### 🎨 Visual Workflow Builder
- **Intuitive Canvas**: Drag-and-drop interface powered by **React Flow**.
- **Real-time Observability**: Live execution logs streamed directly to the UI via WebSockets.
- **Advanced Logic**: Built-in support for parallel execution, loops, and conditional branching.
- **40+ Pre-built Nodes**: A massive library of triggers and actions ready to use.

### 🤖 AI Native Capabilities
- **Multi-LLM Support**: Seamless switching between OpenAI, Anthropic, and Google AI.
- **AI-Assisted Creation**: Describe your goal in natural language and watch Fuse build the workflow for you.
- **Cost Monitoring**: Automatic tracking of token usage and execution costs.
- **Human-in-the-loop**: Pause execution for manual approval or input.

### 🏗️ Modular Ecosystem
- **`node_packages/`**: A standard for defining workflow nodes with isolated requirements and backend logic.
- **`plugin_packages/`**: Extend the core platform with custom services, UI panels, and background processes.

---

## 📦 Getting Started

The recommended way to install and run Fuse is using **[uv](https://github.com/astral-sh/uv)** for high-performance Python management.

### 1. Installation

```bash
uv pip install fuse-io
```

### 2. Initialize Project

```bash
# Set up your environment and initial database
fuse init
```

### 3. Launch the Engine

```bash
# Start the backend server and frontend dashbard
fuse start
```

Your dashboard will be available at **`http://localhost:5678`** 🚀

---

## 🏗️ Architecture

Fuse uses a decoupled, three-tier architecture designed for speed and reliability.

```text
┌──────────────────────────────────────────┐
│          Dashboard (Next.js)             │
│   - Visual Builder | Real-time Logs      │
│   - Node Management | Credentials        │
└───────────────────┬──────────────────────┘
                    │ REST + WebSockets
┌───────────────────▼──────────────────────┐
│          Core Engine (FastAPI)           │
│   - JWT Auth | Workflow Orchestrator     │
│   - Plugin Discovery | Node Execution     │
└─────────┬────────────────────────┬───────┘
          │                        │
┌─────────▼─────────┐    ┌─────────▼────────┐
│    SQLModel DB    │    │  Redis + Celery  │
│  (Workflows/Logs) │    │  (Async tasks)   │
└───────────────────┘    └──────────────────┘
```

---

## � The Antigravity Plugin

The **Antigravity** plugin is Fuse's "secret sauce." It allows you to use high-tier models (like Claude 3.5 Sonnet or Gemini 1.5 Pro) using your existing Google AI entitlements by proxying requests through your local machine.

- **Unlock Zero-Cost Pro Tier**: Leverages free-tier or paid entitlements directly through your browser's authenticated session.
- **Local CLIProxyAPI**: A lightweight local server that bridges standard OpenAI/Anthropic API calls to the Antigravity proxy.

---

## 🛠️ Development Setup

If you want to contribute to the core engine or build custom nodes:

### Prerequisites
- Python 3.10+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv)

### Clone and Install
```bash
git clone https://github.com/fuse-io/fuse.git
cd fuse

# Backend Setup
cd fuse_backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Frontend Setup
cd ../fuse_frontend
npm install
npm run dev
```

---

## 🤝 Contributing

We love contributions! Whether it's a new node, a bug fix, or a feature request, feel free to open a PR.

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Built with ⚡ by [Bibek Timilsina](https://github.com/bibektimilsina)**
*Keep your workflows in constant fuse* 🌊
