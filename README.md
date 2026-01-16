# 🚀 Fuse - Workflow Automation in Flux

[![PyPI version](https://badge.fury.io/py/fuse.svg)](https://badge.fury.io/py/fuse)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Fuse** is a powerful **local-first** workflow automation platform with visual builder, AI integration, and extensive node library. Build complex automations with a drag-and-drop interface, similar to n8n and Zapier, but optimized for local deployment and AI-powered workflows.

> **"Keep your workflows in constant flux"** ⚡

## ✨ Features

### 🎨 Visual Workflow Builder
- **Drag-and-drop** interface powered by React Flow
- Real-time workflow execution with live log streaming
- Support for parallel execution, loops, and conditional branching
- **29+ pre-built nodes** including triggers, actions, AI, and logic nodes

### 🤖 AI-Powered Automation
- Built-in **AI LLM nodes** supporting OpenAI, Anthropic, and Google AI
- **AI Agent** nodes for autonomous task completion
- AI-assisted workflow generation from natural language prompts
- Token usage tracking and cost monitoring

### 🔌 Extensive Integration Library
- **Triggers**: Manual, Cron, Webhook, Email, Form, RSS, WhatsApp
- **Actions**: HTTP requests, Google Sheets, Slack, Discord, Email
- **Logic**: Conditions, Switch/Case, Loops, Merge, Delay, Pause
- **Data**: Transform, Store, Set Variables
- **Code**: Python and JavaScript execution nodes

### 🔒 Security & Performance
- **JWT-based authentication** with secure session management
- **Rate limiting** and **circuit breaker** patterns for external API calls
- **PostgreSQL** database with Alembic migrations
- **Redis** for caching and Celery task queue
- **WebSocket support** for real-time updates

## 📦 Installation

### Quick Start

```bash
pip install fluxo
```

### Initialize and Start

```bash
# Initialize configuration
fluxo init

# Start the server
fluxo start
```

Then open your browser to `http://localhost:8000` 🎉

### Custom Configuration

```bash
fluxo start --host 0.0.0.0 --port 3000 --workers 4 --reload
```

## 🛠 Development Setup

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend development)

### Clone and Install

```bash
git clone https://github.com/fuse-io/fuse.git
cd fuse

# Backend setup
cd fuse_backend
pip install -e ".[dev]"

# Frontend setup
cd ../fuse_frontend
npm install
npm run dev
```

### Environment Configuration

Create a `.env` file in the `fuse_backend` directory:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/fluxo

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production

# AI API Keys (Optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# OAuth (Optional)
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
SLACK_OAUTH_CLIENT_ID=...
SLACK_OAUTH_CLIENT_SECRET=...
```

### Run with Docker

```bash
docker-compose up --build
```

Access the application at `http://localhost:8000`

## 📚 Usage Examples

### Creating Your First Workflow

1. **Add a Trigger**: Start with a Manual Trigger, Webhook, or Cron Schedule
2. **Add Actions**: Connect HTTP Request, Google Sheets, or AI nodes
3. **Add Logic**: Use conditions, loops, or parallel branches
4. **Test & Deploy**: Click "Execute" to test, then activate for production

### Example: AIowered Data Processing

```python
# Workflow structure:
# Trigger (Manual) → HTTP Request → AI LLM → Transform → Google Sheets
```

1. Fetch data from an API
2. Process with AI (summarize, classify, extract)
3. Transform the results
4. Save to Google Sheets

### Example: Scheduled Report Generation

```python
# Workflow structure:
# Cron Trigger → Read Sheets → Loop → AI Agent → Email
```

1. Run daily at 9 AM
2. Read data from Google Sheets
3. Loop through each row
4. Generate insights with AI
5. Send email report

## 🏗 Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (Next.js)              │
│   - React Flow Workflow Builder         │
│   - Real-time Logs (WebSocket)          │
│   - Node Configuration UI                │
└──────────────────┬──────────────────────┘
                   │ HTTP + WebSocket
┌──────────────────▼──────────────────────┐
│         Backend (FastAPI)               │
│   - REST API (JWT Auth)                 │
│   - WebSocket for live logs             │
│   - Workflow Engine                     │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼─────────┐
│   PostgreSQL   │   │   Redis + Celery │
│  (Workflows &  │   │  (Task Queue &   │
│   Executions)  │   │     Cache)       │
└────────────────┘   └──────────────────┘
```

## 🚀 CLI Commands

```bash
# Start server
fluxo start [--host HOST] [--port PORT] [--workers N] [--reload]

# Initialize project
fluxo init

# Show version
fluxo version

# Help
fluxo --help
```

## 🔐 Security Best Practices

1. **Change default SECRET_KEY** in production
2. Use **environment variables** for sensitive data
3. Enable **rate limiting** for public endpoints
4. Use **HTTPS** in production deployments
5. Regularly **rotate API keys** and credentials

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Workflow

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [n8n](https://n8n.io/) and [Zapier](https://zapier.com/)
- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [React Flow](https://reactflow.dev/)
- Based on [full-stack-fastapi-template](https://github.com/tiangolo/full-stack-fastapi-template)

## 📞 Support

- 📖 [Documentation](https://github.com/fuse-io/fuse#readme)
- 🐛 [Issue Tracker](https://github.com/fuse-io/fuse/issues)
- 💬 [Discussions](https://github.com/fuse-io/fuse/discussions)

---

**Made with ⚡ by [Bibek Timilsina](https://github.com/bibektimilsina)**

*Fluxo - Keep your workflows in constant flux* 🌊
