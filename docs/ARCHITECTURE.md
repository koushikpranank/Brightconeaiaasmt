# System Architecture & Technical Specifications

This document provides a comprehensive technical blueprint of the **Agentic AI Supply Chain Disruption Monitoring System**, detailing service components, data flows, 7-agent LangGraph workflow orchestration, domain models, and system sequence diagrams using Mermaid UML format.

---

## 1. System Architecture Component Diagram (UML)

```mermaid
componentDiagram
    package "External Data Sources & Integrations" {
        [Supplier Status Feed] as SUP_FEED
        [Logistics Carrier API] as LOG_FEED
        [Inventory Snapshots] as INV_FEED
        [Open-Meteo Weather API] as WX_API
    }

    package "FastAPI Backend Service" {
        [APScheduler Daemon] as SCHED
        [REST API Router] as API_ROUTER
        [PDF Report Generator] as PDF_GEN
        
        package "LangGraph Agent Engine" {
            [1. Monitoring Agent] as AGENT_1
            [2. Detection Agent] as AGENT_2
            [3. Inventory & Demand Agent] as AGENT_3
            [4. Impact Assessment Agent] as AGENT_4
            [5. Mitigation Agent] as AGENT_5
            [6. Alert & Response Agent] as AGENT_6
            [7. Reviewer / Critic Agent] as AGENT_7
        }

        package "Deterministic Calculation Tools" {
            [Inventory Math Engine] as MATH_INV
            [Supplier Scoring Engine] as MATH_SUP
        }

        [SQLModel Engine] as ORM
    }

    database "Persistence Layer" {
        [(SQLite / PostgreSQL DB)] as DB
    }

    package "React Executive Dashboard" {
        [Control Center UI] as FE_UI
        [Disruption Simulator Widget] as SIM_UI
    }

    actor "Supply Chain Manager" as HUMAN

    %% Connectivity Relationships
    SUP_FEED --> SCHED
    LOG_FEED --> SCHED
    INV_FEED --> SCHED
    WX_API --> AGENT_1

    SCHED --> AGENT_1
    AGENT_1 --> AGENT_2
    AGENT_2 --> AGENT_3
    AGENT_3 --> AGENT_4
    AGENT_4 --> AGENT_5
    AGENT_5 --> AGENT_6
    AGENT_6 --> AGENT_7

    AGENT_3 ..> MATH_INV : Uses
    AGENT_5 ..> MATH_SUP : Uses
    AGENT_7 ..> MATH_INV : Re-verifies

    LangGraph Agent Engine <--> ORM
    ORM <--> DB
    API_ROUTER <--> ORM
    API_ROUTER --> PDF_GEN
    FE_UI <--> API_ROUTER
    SIM_UI --> API_ROUTER
    HUMAN <--> FE_UI
    API_ROUTER -. Approval Gate .-> HUMAN
```

---

## 2. 7-Agent LangGraph State Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    participant Sweep as APScheduler Sweep
    participant A1 as 1. Monitoring Agent
    participant A2 as 2. Detection Agent
    participant A3 as 3. Inventory Agent
    participant A4 as 4. Impact Agent
    participant A5 as 5. Mitigation Agent
    participant A6 as 6. Alert Agent
    participant A7 as 7. Reviewer Agent
    participant DB as Context Lake (Postgres/SQLite)
    participant Manager as Human Approver

    Sweep->>A1: Execute scan_for_changes()
    A1->>A1: Re-check live observations (PO, Logistics, Weather)
    A1->>A2: Pass CaseState with _observations
    
    alt Delivery restored or signal false alarm
        A2->>A2: Re-confirmation fails (_confirmed=False)
        A2->>DB: Set case status="resolved" (TC-05)
        A2-->>Sweep: Terminate execution graph
    else Confirmed Disruption Signal
        A2->>A3: Pass confirmed CaseState (_confirmed=True)
        A3->>A3: Call calculate_inventory_coverage() math tool
        A3->>A4: Pass inventory_analysis (coverage_days, stockout_date)
        A4->>A4: Cross-reference Production Orders & Customers
        A4->>A5: Pass impact (severity, mitigation_window_days)
        A5->>A5: Score & rank approved alternative suppliers
        A5->>A6: Pass mitigation strategy & supplier options
        A6->>A6: Deduplicate alert & dispatch notifications
        A6->>A7: Pass complete case state for audit
        
        alt Issues detected & revision_count < 2
            A7->>A3: Re-route back to target agent (revision loop)
        else Verified & Approved
            A7->>DB: Persist status="pending_approval"
            A7->>Manager: Create ApprovalRequest entry
        end
    end

    Manager->>DB: Submit POST /api/approvals/{id}/decision ("approved")
    DB->>DB: Update Case Status="approved" & trigger execution
```

---

## 3. Class Diagram for Domain Entities (UML)

```mermaid
classDiagram
    class Supplier {
        +int id
        +string supplier_code
        +string name
        +string material
        +int lead_time_days
        +float price_per_unit
        +string currency
        +float available_quantity
        +bool approved
        +bool is_primary
        +string status
    }

    class InventoryItem {
        +int id
        +string material
        +string unit
        +float current_quantity
        +float daily_consumption
        +float required_quantity
        +float reorder_point_days
        +datetime snapshot_at
    }

    class PurchaseOrder {
        +int id
        +string po_number
        +string material
        +string supplier_code
        +float quantity
        +date original_delivery_date
        +date revised_delivery_date
        +string status
    }

    class DisruptionCase {
        +int id
        +string case_number
        +int event_id
        +string status
        +dict inventory_analysis
        +dict impact
        +list supplier_options
        +dict mitigation
        +dict review
        +int revision_count
        +datetime created_at
    }

    class Alert {
        +int id
        +string dedup_key
        +int case_id
        +string disruption_type
        +string material
        +string source
        +string responsible_team
        +string status
        +int occurrence_count
    }

    class ApprovalRequest {
        +int id
        +int case_id
        +string action_type
        +string description
        +float estimated_cost
        +string status
        +string decided_by
        +datetime decided_at
    }

    DisruptionCase "1" -- "1" Alert : generates
    DisruptionCase "1" -- "0..1" ApprovalRequest : requires
    PurchaseOrder "*" -- "1" Supplier : places_with
    InventoryItem "1" -- "*" DisruptionCase : monitors
```

---

## 4. Disruption Detection & Inventory Runway Activity Diagram (UML)

```mermaid
stateDiagram-v2
    [*] --> ScanSources : Monitoring Sweep
    
    state ScanSources {
        [*] --> CheckPOs : Query delayed POs
        CheckPOs --> CheckShipments : Query logistics API
        CheckShipments --> CheckStock : Query low stock items
        CheckStock --> CheckSuppliers : Query unavailable suppliers
    }
    
    ScanSources --> EvaluateCandidate
    
    state EvaluateCandidate {
        [*] --> ReconfirmSignal
        ReconfirmSignal --> CheckRevisedDate : Is PO delayed?
        CheckRevisedDate --> CalculateSlipDays
        
        alt Slip Days <= 0 (Restored)
            CalculateSlipDays --> MarkResolved : Auto-resolve Case
        else Slip Days > 0
            CalculateSlipDays --> CalculateRunway
        end
    }
    
    state CalculateRunway {
        [*] --> CheckSnapshotTimestamp
        
        alt Snapshot Missing
            CheckSnapshotTimestamp --> SetCalculableFalse : stockout_date = null
        else Snapshot Available
            CheckSnapshotTimestamp --> StockoutMath : stockout = snapshot + (quantity / consumption)
        end
        
        StockoutMath --> CheckCoverageGap : stockout_date < revised_delivery_date?
    }
    
    MarkResolved --> [*]
    CheckCoverageGap --> RankAlternativeSuppliers
    RankAlternativeSuppliers --> RequireHumanApproval
    RequireHumanApproval --> [*]
```

---

## 5. Database Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    SUPPLIER ||--o{ PURCHASE_ORDER : supplies
    INVENTORY_ITEM ||--o{ DISRUPTION_EVENT_RECORD : monitors
    DISRUPTION_EVENT_RECORD ||--|| DISRUPTION_CASE : triggers
    DISRUPTION_CASE ||--o{ AGENT_DECISION_LOG : records
    DISRUPTION_CASE ||--o{ ALERT : dispatches
    DISRUPTION_CASE ||--o| APPROVAL_REQUEST : requires
    DISRUPTION_CASE ||--o{ ACTION_ITEM : assigns

    SUPPLIER {
        int id PK
        string supplier_code UK
        string name
        string material
        int lead_time_days
        float price_per_unit
        bool approved
        bool is_primary
    }

    INVENTORY_ITEM {
        int id PK
        string material UK
        float current_quantity
        float daily_consumption
        float reorder_point_days
        datetime snapshot_at
    }

    DISRUPTION_CASE {
        int id PK
        string case_number UK
        int event_id FK
        string status
        json inventory_analysis
        json impact
        json mitigation
        int revision_count
    }

    ALERT {
        int id PK
        string dedup_key UK
        int case_id FK
        string responsible_team
        int occurrence_count
    }

    APPROVAL_REQUEST {
        int id PK
        int case_id FK
        string status
        string decided_by
        datetime decided_at
    }
```
