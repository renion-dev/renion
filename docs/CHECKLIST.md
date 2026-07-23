# RENION + Opportunity Hunter — Checklist (v1.2.0)

## Core
- [x] Domain models (Object, Event, Payment, Invoice, SocialPost, ScanJob)
- [x] Storage (SQLite + aiosqlite)
- [x] EventBus (async)
- [x] Clean architecture
- [x] Configuration via .env
- [x] Logging
- [x] Git with tags

## Data Collection
- [x] RSS (Hacker News, Reddit, TechCrunch, Product Hunt)
- [x] GitHub Issues (VS Code, React, Next.js, Angular, TensorFlow, Kubernetes, Grafana, Ollama)
- [x] Job boards (Weworkremotely, Himalayas, HireWeb3)
- [x] Deduplication by link

## LLM
- [x] OllamaProvider (local)
- [x] GroqProvider (cloud)
- [x] LLM abstraction

## Hypothesis Generation
- [x] Problem detection with frequency
- [x] MVP description, CTA, hypothesis
- [x] Save to DB (type Hypothesis)
- [x] Invoice creation ($1.69)

## Clustering & Market Assessment
- [x] Clustering (sentence-transformers + KMeans)
- [x] TAM/SAM/SOM estimation via LLM
- [x] Store in metadata

## Landing Pages
- [x] Fixed HTML template
- [x] Modern design (gradients, shadows, responsive)
- [x] Stripe Checkout button ($1.69)
- [x] Save to landings/{id}.html

## Economic Layer
- [x] Payment, Transaction, Invoice
- [x] PaymentProvider abstraction
- [x] SimulatedProvider
- [x] StripeProvider + Stripe Checkout
- [x] PaymentProcessor
- [x] Endpoint `/api/create-checkout-session`

## Advertising (stub)
- [x] AdvertisingManager
- [x] Logging campaigns
- [x] AdCampaign objects in DB

## Social Posting
- [x] Mastodon (active, free)
- [x] Twitter (dry-run)
- [x] Reddit, Hacker News, Medium (dry-run)

## Web Interface
- [x] Landing page for RENION
- [x] Hypothesis list (/hypotheses)
- [x] Hypothesis detail (/hypothesis/{id})
- [x] "Run Scan" button with status
- [x] TAM/SAM display
- [x] Full English localization

## CLI
- [x] Scan all sources
- [x] Logging
- [x] Event handling

## Documentation
- [x] 20+ ADR
- [x] Monetization Strategy
- [x] User Guide
- [x] Status
- [x] Checklist
- [x] Release notes

## Deployment
- [x] Railway deployment
- [x] Environment variables
- [x] Production ready

## To Do (Next)
- [ ] Real Twitter posting (add balance)
- [ ] PostgreSQL migration
- [ ] Email collection
- [ ] Free/Pro/Business plans
