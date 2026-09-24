# FinFlow Architecture

## Core Data Flow

```mermaid
flowchart TD
    A[Source Systems] --> B[Level 0 Ingestion]
    B --> C[Bronze]
    C --> D[Silver]
    D --> E[Gold]
    E --> F[Analytics]

    G[Incremental Processing] -.-> B
    H[MERGE / Upsert] -.-> D
    I[Data Quality Gates] -.-> D
    J[Lakeflow Jobs / Orchestration] -.-> B
    J -.-> C
    J -.-> D
    J -.-> E
    J -.-> F
    K[Monitoring / Logging] -.-> J
    L[Performance Optimization] -.-> C
    L -.-> D
    L -.-> E
    M[Unity Catalog / Governance] -.-> C
    M -.-> D
    M -.-> E
```

## Databricks Workflow

```text
level_0_ingestion [SQL Query]
        ↓
bronze_processing [Notebook]
        ↓
silver_processing [Notebook]
        ↓
gold_processing [Notebook]
        ↓
analytics_processing [Notebook]
```

## Layer Responsibilities

| Layer | Main responsibility |
|---|---|
| Level 0 | Initial ingestion and source inspection |
| Bronze | Preserve incoming data and profile quality |
| Silver | Clean, standardize, validate and deduplicate |
| Gold | Create business-oriented datasets |
| Analytics | Answer business questions |
| Engineering | Operationalize and productionize the pipeline |
