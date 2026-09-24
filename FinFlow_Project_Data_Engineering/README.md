# FinFlow — Financial Data Engineering Project

An end-to-end financial data engineering pipeline built with **Databricks, Delta Lake and SQL**, using intentionally messy synthetic banking data.

## Project Overview

FinFlow simulates a financial data platform that receives data from systems such as core banking, card processing, UPI and ATM systems. The project demonstrates how raw source data can be ingested, cleaned, modeled, analyzed and operationalized as a production-style data pipeline.

The project was designed around a layered architecture:

```text
Sources
   ↓
Level 0 — Ingestion
   ↓
Bronze — Raw / near-raw data
   ↓
Silver — Cleaned and standardized data
   ↓
Gold — Business-ready data models
   ↓
Analytics — Business analysis
```

Engineering controls surround the pipeline:

```text
Incremental Processing
        +
MERGE / Upsert
        +
Data Quality Gates
        +
Workflow Orchestration
        +
Failure / Retry Handling
        +
Monitoring & Logging
        +
Performance Optimization
        +
Governance concepts
```

## Technology Stack

- Databricks
- Apache Spark / Spark SQL
- SQL
- Delta Lake
- Databricks Volumes
- Databricks Lakeflow Jobs
- Unity Catalog concepts
- Python notebook source format
- Git / GitHub

## Data Layers

### 1. Level 0 — Ingestion

The Level 0 SQL query reads the source files and performs initial inspection/count checks before the data enters the Bronze layer.

### 2. Bronze

Bronze preserves source information while adding ingestion metadata and performing initial data profiling.

Bronze datasets include:

- customers
- accounts
- transactions
- merchants
- branches
- aml_alerts
- data quality profile

### 3. Silver

Silver creates trusted, standardized datasets through:

- trimming and standardizing strings
- timestamp/date conversion
- numeric type handling
- duplicate detection and canonicalization
- relationship validation
- consistent business values

Final Silver grain/counts:

| Dataset | Rows |
|---|---:|
| customers | 50,000 |
| accounts | 75,000 |
| transactions | 1,000,000 |
| merchants | 10,000 |
| branches | 500 |
| aml_alerts | 20,000 |

### 4. Gold

Gold models the data at business-friendly grains:

- `customer_360`
- `transaction_analytics`
- `aml_risk`
- `account_analytics`
- `branch_performance`

Gold validation confirmed the expected grains:

- 50,000 customers
- 1,000,000 transactions
- 20,000 AML alerts
- 75,000 accounts
- 500 branches

### 5. Analytics

The Analytics layer contains SQL analysis for:

- customer segment analysis
- customer risk analysis
- transaction status
- transaction channels
- transaction types
- branch performance
- AML severity and case status
- high-risk customers with AML alerts
- monthly transaction trends
- top customers by transaction value
- merchant category analysis
- financial/data-quality risk
- unmapped merchant impact

## Data Quality Challenges

The source data intentionally contains realistic data-quality problems.

### Duplicate records

Examples found during profiling:

- customers: 250 duplicate IDs
- accounts: 375 duplicate IDs
- transactions: 5,000 duplicate IDs
- merchants: 50 duplicate IDs
- branches: 2 duplicate IDs
- AML alerts: 100 duplicate IDs

Duplicates were analyzed for exact versus conflicting records and canonicalized using SQL/window-function logic where appropriate.

### Unmapped merchants

The Gold transaction model identified **2,502 transactions with unmapped merchant references**.

Instead of dropping these records, the pipeline preserves them with a `LEFT JOIN` and an `is_unmapped_merchant` flag.

### Null transaction amounts

There are **2,488 transactions with null amounts** in the cleaned transaction data.

These are treated as a data-quality finding rather than blindly replacing the values with zero, because the correct business treatment depends on the source/business rules.

## Engineering Demonstrations

The Engineering notebook demonstrates production-oriented patterns including:

### Incremental Processing

A control-table approach was used to demonstrate detection of unprocessed batches. The existing dataset did not contain trustworthy historical batch metadata, so a small simulated batch was used rather than pretending the existing data had multiple historical ingestion batches.

### MERGE / Upsert

A Delta `MERGE` demonstration shows how:

- matched records are updated
- new records are inserted
- duplicate source keys are resolved before the merge
- rerunning the merge remains idempotent

### Data Quality Gates

Critical quality rules check items such as:

- null transaction IDs
- null customer IDs
- null account IDs
- invalid transaction statuses
- duplicate transaction IDs

Invalid records can be quarantined with a rejection reason and timestamp.

### Workflow Orchestration

The production pipeline was orchestrated with Databricks Jobs / Lakeflow Jobs using task dependencies:

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

The complete workflow was successfully executed.

## Example Analytical Findings

- `CARD_PURCHASE` is the highest-volume transaction type in the dataset.
- `ATM_WITHDRAWAL` and `CASH_DEPOSIT` have substantially higher average successful transaction values than card/UPI/bank-transfer transactions.
- Monthly transaction activity is broadly stable across the main 2025 month buckets.
- High transaction value can result from either transaction frequency or high average ticket size.
- Merchant categories have relatively similar average successful transaction values, making volume a major driver of category-level totals.
- Unmapped merchant transactions represent approximately 0.25% of transactions and are retained rather than silently discarded.

## Repository Structure

```text
FinFlow_Project_Data_Engineering/
│
├── 01_Level_0/
│   └── level_0_ingestion.sql
│
├── 02_Bronze/
│   └── Bronze_FinFlow_Project.py
│
├── 03_Silver/
│   └── Silver_FinFlow_Project.py
│
├── 04_Gold/
│   └── Gold_FinFlow_Project.py
│
├── 05_Analytics/
│   └── Analytics_FinFlow_Project.py
│
├── 06_Engineering/
│   └── Engineering_FinFlow_Project.py
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── interview_notes.md
│
├── .gitignore
└── README.md
```

## Reproducing the Project

The repository contains the transformation and analysis code. The synthetic source data itself is **not committed to GitHub**.

The notebooks reference Databricks Volumes such as:

```text
/Volumes/Finflow_Project_catalog/bronze/raw_files/
```

To reproduce the pipeline, the source files must be made available in the corresponding Databricks environment and the required catalog/schema permissions must be configured.

## Interview Story

A concise way to describe the project:

> FinFlow is a financial data engineering pipeline built on Databricks using synthetic banking data. I designed a layered architecture from ingestion through Bronze, Silver, Gold and Analytics. Silver handles standardization, type conversion, timestamp parsing, deduplication and relationship validation, while Gold creates business-oriented datasets such as Customer 360, transaction analytics and AML risk. I also implemented engineering patterns including incremental processing, Delta MERGE, data-quality gates and workflow orchestration. One example challenge was unmapped merchant references; instead of dropping those transactions, I preserved them with a LEFT JOIN and a data-quality flag. The final pipeline was orchestrated with task dependencies and successfully executed in Databricks.

## Important Note

This project uses synthetic data for learning and portfolio purposes. It is not connected to a real bank or financial institution.
