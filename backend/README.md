# Agentic AI Supply Chain Backend Service

FastAPI backend orchestrating a 7-agent LangGraph workflow pipeline, deterministic inventory math, automated background monitoring sweeps, and human-in-the-loop approval gates.

## Core Components

- **7-Agent LangGraph StateGraph (`app/agents/graph.py`)**: Shared `CaseState` pipeline driving cases through Monitoring -> Detection -> Inventory Math -> Impact Assessment -> Alternative Mitigation -> Alerting -> Reviewer Audit.
- **Deterministic Math Engine (`app/tools/`)**:
  - `inventory_math.py`: Pure functions computing runway coverage days (`current_quantity / daily_consumption`), projected stockout date (`snapshot_at + coverage_days`), mitigation window days (`stockout_date - today`), and severity.
  - `supplier_compare.py`: Pure functions scoring and ranking approved alternative suppliers (`lead_time * 1.0 + price * 0.1`).
- **Pluggable LLM Integration (`app/llm.py`)**: Uses LLM **only** for natural-language narration; all numbers are passed in from deterministic math tools. Default provider is `mock` (zero network calls, zero API keys).
- **APScheduler Monitoring Sweep (`app/scheduler.py`)**: Runs periodic sweeps (`MONITOR_INTERVAL_SECONDS`, default 60s) scanning all sources for new candidates and re-checking open cases to auto-resolve cleared signals (TC-05).
- **PDF Report Generator (`app/reports/pdf_generator.py`)**: Formats disruption case summaries into downloadable PDF reports.

## Project Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── graph.py             # LangGraph 7-agent pipeline assembly & execution
│   │   ├── state.py             # CaseState TypedDict & audit logging helper
│   │   ├── monitoring_agent.py  # Agent 1: Re-checks live observations
│   │   ├── detection_agent.py   # Agent 2: Confirms signals or auto-resolves
│   │   ├── inventory_agent.py   # Agent 3: Invokes deterministic runway math
│   │   ├── impact_agent.py      # Agent 4: Evaluates downstream order impact
│   │   ├── mitigation_agent.py  # Agent 5: Ranks alternative suppliers & flags verification
│   │   ├── alert_agent.py       # Agent 6: Dispatches deduplicated team alerts
│   │   └── reviewer_agent.py    # Agent 7: Verifies calculations & loops back if needed
│   ├── api/                     # FastAPI REST API route handlers
│   ├── integrations/            # Supplier, Inventory, Logistics & Weather API clients
│   ├── reports/                 # PDF report generation module
│   ├── services/                # Case runner & sweep orchestration
│   ├── tools/                   # Pure deterministic math functions
│   ├── config.py                # Environment configuration settings
│   ├── database.py              # SQLModel engine & session management
│   ├── llm.py                   # Pluggable LLM narration client
│   ├── main.py                  # FastAPI application entrypoint
│   ├── models.py                # SQLModel ORM entity schemas
│   ├── scheduler.py             # APScheduler background daemon
│   ├── schemas.py               # Pydantic DTO contracts
│   └── seed_data.py             # Worked example demo database seeder
├── tests/                       # Pytest unit & end-to-end integration test suite
├── pytest.ini
└── requirements.txt
```

## Running Backend Locally

1. **Activate Virtual Environment**:
   ```bash
   .\venv\Scripts\activate
   ```

2. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start FastAPI Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **Run Unit & Integration Tests**:
   ```bash
   pytest
   ```
