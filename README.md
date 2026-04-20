# GPS Shield

> Analyzing millions of flight records to map the GPS spoofing crisis — and modeling how next-generation LEO navigation solves it.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![deck.gl](https://img.shields.io/badge/deck.gl-9-000000)](https://deck.gl)

## The Problem

GPS is under attack. State-level actors are deploying GPS spoofing and jamming across conflict zones worldwide — the Baltic Sea, Eastern Mediterranean, Persian Gulf, Red Sea, Black Sea, Ukraine, and the South China Sea. Commercial aviation, maritime shipping, and autonomous systems are all affected. GPS interference incidents have surged dramatically, with some regions seeing hundreds of events per month.

## What GPS Shield Does

- **Detects** GPS spoofing and jamming events by analyzing ADS-B aircraft position reports, using 6 anomaly detectors (impossible velocity, position jumps, altitude divergence, heading mismatches, spatial clustering, and signal loss).
- **Maps** detected interference into geographic zones using DBSCAN clustering, classifies each as spoofing or jamming, and scores severity on a 0-100 scale.
- **Models** how Xona Space Systems' Pulsar LEO constellation would neutralize each threat — with an interactive toggle that shows jamming radii shrink by 97.5% and spoofing eliminated entirely via cryptographic authentication.

## Key Findings

Computed dynamically from loaded data via `compute_findings.py`. Representative results:

| Finding | Value |
|---------|-------|
| GPS Interference Events Detected | ~40,000 across 7 conflict zones |
| Top Affected Region | Baltic Sea — highest concentration of spoofing events |
| Trend | Significant quarter-over-quarter escalation (Q1 2026 vs Q4 2025) |
| Unique Aircraft Affected | Thousands of unique ICAO24 identifiers flagged |
| Pulsar Impact | 100% spoofing eliminated, 97.5% jamming area reduction |

## The Pulsar Solution

Toggle **Pulsar Mode** on the interactive globe to see the difference:

- **GPS Mode:** Full jamming radii, broken flight paths, spoofed positions
- **Pulsar Mode:** Radii shrink by 97.5% (6.3x reduction from ~178x signal strength), all spoofing events eliminated by cryptographic range authentication

This is the "aha moment" — seeing the threat landscape transform when next-gen navigation is applied.

## Architecture

```
  OpenSky Network REST API
         |
         v
  BACKEND (FastAPI)
  ├── Data Ingestion (async poller + batch loader)
  ├── Anomaly Detection Pipeline
  │   └── StateWindow → 6 Detectors → Classifier → Scorer → DBSCAN Clusterer
  ├── Pulsar Mitigation Modeler
  ├── PostgreSQL (anomaly_events, interference_zones, findings, region_stats)
  └── REST API (7 endpoints)
         |
         v
  FRONTEND (Next.js 14)
  ├── 3D Globe (deck.gl) with Pulsar Mode toggle
  ├── Key Findings dashboard with trend charts
  └── Pulsar Explainer with animated comparisons
```

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python 3.12, FastAPI, Uvicorn, SQLAlchemy | Same language for detection math and API serving |
| Database | PostgreSQL 16 (Neon free tier) | Simple, reliable, no extensions needed |
| Frontend | Next.js 14, TypeScript, deck.gl, Tailwind CSS | SSR, App Router, purpose-built geospatial rendering |
| Detection | NumPy, SciPy, scikit-learn | DBSCAN clustering, fast vector math |
| Data Source | OpenSky Network REST API | Free, public ADS-B aircraft data |
| Deployment | Vercel (frontend), Railway (backend) | Free/low-cost, always-on |

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your DATABASE_URL and optional OpenSky credentials

# Run migrations
alembic upgrade head

# Seed demo data (or use load_historical for real data)
python3 -m app.scripts.seed_demo
python3 -m app.scripts.compute_findings

# Start the server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Start development server (backend must be running)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the globe.

## Project Structure

```
backend/
├── app/
│   ├── detection/          # Anomaly detection pipeline
│   │   ├── interfaces/     # Public contracts (Pydantic models)
│   │   └── internal/       # Detectors, classifier, clusterer, scorer
│   ├── pulsar/             # Pulsar mitigation modeler
│   │   ├── interfaces/     # Xona specs and types
│   │   └── internal/       # Mitigation calculations
│   ├── scripts/            # CLI tools (seed, load, compute)
│   ├── api.py              # REST API endpoints
│   ├── config.py           # Environment settings
│   ├── database.py         # Async SQLAlchemy engine
│   ├── ingestion.py        # OpenSky API client
│   ├── models.py           # ORM models
│   └── schemas.py          # Pydantic response schemas
├── tests/                  # pytest suite
└── Dockerfile

frontend/
├── src/
│   ├── app/                # Next.js App Router pages (globe, findings, pulsar, methodology)
│   ├── components/
│   │   ├── globe/          # deck.gl globe, Pulsar toggle, tooltips, error boundary
│   │   ├── dashboard/      # Stats bar, region list, zone detail
│   │   ├── findings/       # Finding cards, trend/region charts
│   │   ├── pulsar/         # Signal comparison, radius animation, jammer sandbox
│   │   └── ui/             # Nav, Footer, welcome modal, creator credit
│   └── lib/                # Types, API client, hooks, constants
└── package.json
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | System health and database status |
| `GET /api/zones/live` | Currently active interference zones |
| `GET /api/zones/history` | Historical zones with filters and pagination |
| `GET /api/zones/{id}` | Zone detail with individual aircraft events |
| `GET /api/stats` | Global dashboard statistics |
| `GET /api/findings` | Pre-computed key findings |
| `GET /api/regions` | Per-region breakdowns with trends |

## Data

The demo deployment uses **synthetic ADS-B data** generated by `seed_demo.py`, modeling realistic GPS interference patterns across 7 known conflict zones over 6 months (Oct 2025 -- Mar 2026). The synthetic data includes realistic geographic distributions, temporal trends, and spoofing/jamming ratios calibrated to published reports.

The platform is also designed to ingest **real aircraft data** from the [OpenSky Network](https://opensky-network.org) via `load_historical.py`. With OpenSky credentials configured, the system fetches real state vectors and runs them through the full detection pipeline.

## About

Built by Larry Zhang

Inspired by [Xona Space Systems](https://www.xonaspace.com)' Pulsar constellation and the growing GPS vulnerability crisis documented by organizations like the [C4ADS GPS Spoofing Report](https://c4ads.org) and [EUROCONTROL](https://www.eurocontrol.int).

## License

MIT
