# Agentic AI Supply Chain Frontend Control Center

A modern, high-contrast, glassmorphic React 18 executive control center built with TypeScript, Tailwind CSS, Recharts, and Lucide React icons.

## Features

- **Executive KPI Control Center**: Real-time summary metrics for active disruptions, open alerts, pending human approvals, and operational action items.
- **At-Risk Material Runway Charts**: Interactive bar charts powered by Recharts visualizing remaining coverage days before stockout.
- **Multi-Agent Pipeline Case Inspector**: Interactive slide-over drawer (`CaseDetailModal`) allowing users to inspect full 7-agent execution states, reviewer audit findings, math trace notes, and scored alternative supplier options.
- **Disruption Simulator**: Single-click modal suite (`SimulationModal`) to test spec worked examples (TC-01 10-day delay injection & TC-05 schedule restoration auto-resolution).
- **Human Approval Portal**: Manager decision submission interface enforcing human approval before committing procurement orders.
- **Operational Action Tracker**: Departmental task board allowing inline status updates (`open` -> `in_progress` -> `done`).
- **Executive PDF Report Export**: One-click download trigger for formatted PDF disruption assessment reports.

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts            # Typed REST API client with error handling & docstrings
│   ├── components/
│   │   ├── Badge.tsx            # Color-coded status badge component with icons
│   │   ├── CaseDetailModal.tsx  # 7-agent pipeline drawer modal
│   │   ├── Layout.tsx           # Master navigation sidebar & header container
│   │   ├── SimulationModal.tsx  # Disruption scenario test simulator modal
│   │   └── StatCard.tsx         # Executive KPI metric card with glowing borders
│   ├── pages/
│   │   ├── ActionTracker.tsx    # Operational action items task board
│   │   ├── Alerts.tsx           # Deduplicated alert stream view
│   │   ├── Dashboard.tsx        # Control center summary view
│   │   ├── ImpactAnalysis.tsx   # Operational impact & runway math view
│   │   ├── Inventory.tsx        # On-hand stock & burn rate monitoring
│   │   ├── Mitigation.tsx       # Alternative supplier comparison & human approval
│   │   ├── Reports.tsx          # PDF assessment report archive
│   │   ├── ShipmentTracking.tsx # Logistics tracking & PO delay simulation
│   │   └── Suppliers.tsx        # Supplier directory & capacity roster
│   ├── styles/
│   │   └── index.css            # Custom CSS framework & executive dark theme tokens
│   ├── types.ts                 # Domain entity TypeScript interfaces with docstrings
│   ├── App.tsx                  # React Router configuration
│   └── main.tsx                 # Application entrypoint
├── package.json
├── tailwind.config.js           # Extended Tailwind configuration
└── vite.config.ts               # Vite build & proxy settings
```

## Running Locally

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Start Dev Server**:
   ```bash
   npm run dev
   ```
   Access application at `http://localhost:5173`.

3. **Production Build**:
   ```bash
   npm run build
   ```
