# RENION — Autonomous Intelligence Network

**RENION** is an operating environment for autonomous agents.  
**Opportunity Hunter** is the first module that automatically finds market opportunities.

## Features

- 🔍 **Data Collection** — 12+ sources (Hacker News, Reddit, GitHub Issues, job boards).
- 🧠 **AI Analysis** — uses Groq (or local Ollama) to identify problems and generate hypotheses.
- 💡 **Hypothesis Generation** — MVP description, CTA, TAM/SAM/SOM estimation.
- 🌐 **Landing Pages** — automatically generates modern landing pages with Stripe Checkout.
- 💰 **Payment Processing** — Stripe Checkout integration ($1.69 per hypothesis).
- 🐘 **Social Posting** — automatically publishes to Mastodon (free) and Twitter (optional).
- 🖥️ **Web Interface** — view hypotheses and run scans from your browser.
- 📦 **CLI** — run scans from the command line.

## Tech Stack

- **Python 3.11+** (FastAPI, asyncio)
- **Database:** SQLite (aiosqlite)
- **LLM:** Groq (cloud) or Ollama (local)
- **Payments:** Stripe Checkout
- **Social:** Mastodon, Twitter (optional)
- **Deployment:** Railway / Render / Vercel (landings)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/renion-dev/renion.git
cd renion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure .env
cp .env.example .env

# Run scan (CLI)
python -m src.interfaces.cli

# Run web server
./start.sh
# or
uvicorn src.interfaces.web:app --host 0.0.0.0 --port 8000 --reload

### 2. Оновлення `docs/STATUS.md`

```bash
cat > docs/STATUS.md <<'EOF'
# RENION + Opportunity Hunter — Status (v1.2.0)

**Date:** 2026-07-23  
**Version:** v1.2.0  

## ✅ Done

- Core architecture (domain, application, infrastructure, interfaces)
- Data collection (RSS, GitHub Issues, job boards)
- LLM abstraction (Ollama + Groq)
- Hypothesis generation with MVP, CTA, TAM/SAM/SOM
- Landing page generation with Stripe Checkout
- Payment processing ($1.69 via Stripe)
- Social posting (Mastodon – free, Twitter – dry-run)
- Web interface (landing, hypotheses, scan, details)
- CLI for scanning
- Deployment on Railway (production-ready)
- Documentation (ADR, User Guide, Monetization Strategy)

## ❌ To Do

- Real Twitter posting (needs balance top-up)
- Email collection (optional)
- PostgreSQL migration (for production)
- Rate limiting & user accounts (Free/Pro/Business)

## Deployment

- **URL:** https://renion-production.up.railway.app
- **LLM:** Groq (cloud) with fallback to Ollama (local)
- **Payments:** Stripe Checkout (test mode)
- **Social:** Mastodon (active), Twitter (dry-run)

## Next Steps

- Activate Twitter (add balance)
- Collect user feedback
- Add PostgreSQL for production
# Updated
