# Phase 3 — Live Prep Layer (STUB MODE)

This module prepares the entire system for the transition from STUB_MODE to LIVE_MODE.

## Purpose
Phase 3 does NOT activate any real API, workers, routers, ML models, or secrets.
It only defines the architecture, folders, contracts, and integration points required for LIVE mode.

## Components

### 1. live_config.py
Defines STUB_MODE and LIVE_MODE flags.
Default: STUB_MODE=True, LIVE_MODE=False.

### 2. env_loader.py
Documentation-only module explaining required env variables when LIVE_MODE is activated.

### 3. safe_routing.py
Router registry placeholder — not registered in main.py in Phase 3.

### 4. brain/
Registry for ML "brains" that will be filled in Phase 4.

### 5. ad_integrations/
Stub adapters for:
- Meta Ads
- TikTok Ads
- Spotify Ads
- YouTube Ads

Each adapter defines the same contract to ensure compatibility in Phase 4.

### 6. workers_blueprints/
Blueprints for workers and asynchronous jobs (no workers activated yet).

### 7. ml_models/
Directory structure for ML models (YOLO, COCO, Ultralytics) without loading any real weights.

## Guarantees
- No API keys loaded
- No external HTTP calls executed
- main.py untouched
- migrations untouched
- Phase1/Phase2 modules untouched
- 100% safe scaffolding

Phase 4 will activate LIVE integrations using this scaffolding.
