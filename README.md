# NomosFlow

**AI-powered dunning and churn prevention engine for white-label energy retailers.**

Built as a full-stack demonstration of the operational back-office intelligence layer that Nomos deploys across its partner network - the kind of zero-to-one internal tooling that separates a scaled energy retailer from one that bleeds revenue on failed payments and reactive churn.

---

## The Problem

Nomos exists to eliminate energy costs for 200 million European households. It does this by enabling non-energy companies - EV manufacturers, heat pump installers, battery storage OEMs - to offer their own branded dynamic electricity tariffs within 7 days via a single API integration.

At scale, three things break the unit economics of any energy retailer:

| Problem | Industry Reality |
|---|---|
| Failed payment cycles | 3–8% of monthly revenue at risk from dunning failures |
| Reactive churn management | By the time a customer cancels, the window to recover them has passed |
| Generic outreach | Boilerplate "payment failed" emails drive ~12% open rates and accelerate cancellations |

NomosFlow solves all three in a single operational layer, powered by Gemini AI.

---

## What NomosFlow Does

### Intelligent Dunning
When a direct debit fails, NomosFlow doesn't blast a generic retry. It uses Gemini to classify the *reason* for the failure - `insufficient_funds`, `expired_card`, `bank_block`, `sepa_reject` - with a confidence score and a plain-English explanation. The retry scheduler then picks the optimal retry date based on the customer's salary day, contract age, and failure pattern, not a fixed 3-day rule.

### Predictive Churn Scoring
NomosFlow runs a churn model across the customer base before customers cancel. Each customer gets a scored risk level (`low` / `medium` / `high` / `critical`) derived from failed payment frequency, days since last successful payment, retry exhaustion percentage, contract age, and device type. The scoring is enriched by Gemini reasoning - not a black-box number, but an explanation of *why* a customer is at risk and what action to take.

### AI Retention Messaging
For at-risk customers, NomosFlow generates personalised retention messages that reference the customer's specific device (EV, heat pump, battery), their actual energy savings in EUR, and upcoming cheap tariff windows. Device-aware personalisation has demonstrated 3× better retention outcomes versus generic outreach in comparable energy/fintech contexts.

### White-Label Partner View
Nomos operates a B2B white-label model. NomosFlow's partner switcher lets operators toggle between partner brands - "Müller Wärmepumpen GmbH", "VoltDrive EV", "SolarBank Energy" - to see customer portfolios, risk distributions, and dunning queues scoped to each OEM partner's brand.

### Real-Time AI Pipeline
The dunning cycle runs live in the UI. Hit "Run Dunning Cycle" and watch Gemini process customers in sequence - classifying failures, scheduling retries, generating messages - with real-time progress feedback.

---

## Architecture

```
nomosflow/
├── backend/          # FastAPI + PostgreSQL + Gemini AI
└── frontend/         # Next.js 14 + Tailwind CSS
```

### Backend - FastAPI

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 |
| Database | PostgreSQL via SQLAlchemy 2.0 |
| Migrations | Alembic |
| AI | Google Gemini 1.5 Flash (`google-generativeai`) |
| Validation | Pydantic v2 + pydantic-settings |
| Testing | pytest + pytest-asyncio |

**API surface:**

| Route | Purpose |
|---|---|
| `GET /api/partners` | List all OEM partners |
| `GET /api/customers` | Customer list with filter support |
| `GET /api/customers/{id}/full-profile` | Full customer profile with payment history + churn score |
| `GET /api/payments` | Payment records across all customers |
| `POST /api/dunning/run-cycle` | Trigger full AI dunning cycle |
| `GET /api/dunning/timeline/{customer_id}` | Dunning action history per customer |
| `GET /api/churn/scores` | All churn scores, sorted by risk |
| `POST /api/churn/score-all` | Re-score all active customers via Gemini |
| `POST /api/ai/retention-message` | Generate personalised retention message |
| `POST /api/ai/classify-failure` | Classify a payment failure reason |

**Data model (PostgreSQL):**

```
partners        → OEM white-label clients (device_type, brand_color, slug)
customers       → End customers with device, tariff, salary_day, annual_saving_eur
payments        → Monthly billing records (status, failure_reason, retry_count, next_retry_date)
dunning_actions → Full audit log of every dunning step taken (AI or manual)
churn_scores    → Latest Gemini-scored churn risk per customer (score, risk_level, factors JSONB)
```

### Frontend - Next.js

| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| Icons | Lucide React |
| Type Safety | TypeScript throughout |

**Pages:**

| Route | What it shows |
|---|---|
| `/dashboard` | KPI summary cards, top at-risk customers, recent payment feed, partner breakdown |
| `/customers` | Filterable customer table with inline risk badges; click opens a slide-out drawer with full profile + payment timeline + churn score |
| `/dunning` | Failed/retrying payment queue; "Run Dunning Cycle" button with live progress |
| `/retention` | Grid of AI-generated retention messages per at-risk customer |
| `/partners` | Partner cards with white-label preview and brand switcher |

**Design system 
The UI is built on a warm off-white (`#F9F7F2`) base with a serif heading font (Lora), olive green CTAs (`#3D6B2C`), macOS-style window chrome on cards, and status pills for payment state and churn risk. Clean, opinionated, and distinct from generic dashboard templates.

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (local or Docker)

## Project Context

This project was built as a working demonstration of the kind of product engineering Nomos does internally - ownership of zero-to-one operational problems end-to-end, AI-native tooling as a default rather than an afterthought, and a high bar for craft in both the system design and the user experience.

The brief was simple: build the internal back-office tool that Nomos needs as it scales its partner network from 3 OEMs to 30. Everything - problem scoping, architecture, schema design, backend services, frontend components, AI prompt engineering - was built from a blank slate.

---

## License

Private. Built for Nomos.
