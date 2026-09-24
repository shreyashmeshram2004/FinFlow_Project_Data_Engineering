# FinFlow — Financial Data Engineering Pipeline

End-to-end financial data engineering project built with Databricks, Delta Lake, SQL and Apache Spark

FinFlow is a portfolio data engineering project built around a synthetic banking dataset.

The goal of the project was to take data that looks closer to what you might receive from multiple financial systems — including duplicates, missing values, inconsistent timestamps, conflicting records and incomplete relationships — and turn it into structured, validated and analytics-ready data.

The project covers the complete journey from raw source data → ingestion → data quality → transformation → business data models → analytics → workflow orchestration.

The implementation is primarily SQL-based and uses Databricks and Delta Lake throughout the pipeline.

# What I Built

The overall pipeline follows a layered architecture:

Source Systems
    |
    
Level 0 - Ingestion
    |
    
Bronze - Raw & Profiled Data
    |
    
Silver - Cleaned & Validated Data
    |
    
Gold - Business Data Models
    |
    
Analytics
    |
    
Databricks Jobs / Workflow Orchestration

The pipeline is then orchestrated using Databricks Jobs, with each layer depending on the successful completion of the previous layer.

# 1. Project Context

Financial systems rarely produce perfectly clean datasets.

A transaction may reference a customer correctly but contain a missing amount. A merchant ID may exist in the transaction system but not in the merchant master table. The same transaction may appear more than once because of duplicate ingestion. Different systems may also represent the same timestamp or categorical value differently.

Instead of starting with a clean dataset, FinFlow was designed around these types of problems.

The source data was intentionally generated with issues so that the project could demonstrate actual data engineering work rather than only simple SELECT, JOIN and GROUP BY operations.

Source datasets

The project contains six primary datasets:

Customers
Accounts
Transactions
Merchants
Branches
AML Alerts

These datasets are related to each other through customer, account, merchant and branch relationships.

# 2. Dataset Scale

The source data contained more than 1.1 million records across the six datasets.

## Dataset

The project contains six primary financial datasets. The source data was intentionally generated with duplicate records and other data-quality issues. The Silver layer removes duplicate business keys and produces the final trusted record counts.

| Dataset | Source Records | Final Records | Records Removed |
|---|---:|---:|---:|
| Customers | 50,250 | 50,000 | 250 |
| Accounts | 75,375 | 75,000 | 375 |
| Transactions | 1,005,000 | 1,000,000 | 5,000 |
| Merchants | 10,050 | 10,000 | 50 |
| Branches | 502 | 500 | 2 |
| AML Alerts | 20,100 | 20,000 | 100 |

The reduction was primarily caused by duplicate records rather than arbitrary filtering.

This became an important part of the project because the objective was not simply to reduce row counts. The objective was to establish the correct business grain and uniqueness for downstream processing.

# 3. Source Data Problems

Before building the transformation layers, the source data was profiled to understand what was actually coming into the pipeline.
Some of the issues identified included:

### Duplicate records

The transaction dataset contained:
**1,005,000 raw records**
but only:
**1,000,000 unique transaction IDs**
That means there were **5,000 duplicate transaction IDs**.
Further investigation showed:

```
```

```
Transaction duplicate IDs
│
├── 4,900 exact duplicates
│
└── 100 conflicting duplicates
```

The conflicting records were more interesting because the duplicate ID did not necessarily represent identical rows.
Similar duplicate patterns were found in the other datasets.

### Missing values

The transaction data contained:
**2,488 records with NULL transaction amounts**
These were not automatically converted to zero because a missing financial value and a zero-value transaction represent different business meanings.

### Negative values

There were:
**245 transactions with negative amounts**
These were retained and flagged for analysis rather than automatically deleted.

### Incomplete relationships

The transaction dataset also contained transactions referencing merchants that could not be found in the merchant master data.
After the final transformations, **2,502 transactions had unmapped merchant references**.
Instead of deleting these transactions, the pipeline preserved them and explicitly identified the relationship problem.

---

# 4. Level 0 — Ingestion

The Level 0 layer establishes the initial ingestion boundary for the source files.
The source transaction data represented multiple financial systems:

```
```

```
CORE_BANKING
CARD_PROCESSOR
UPI_SWITCH
ATM_SWITCH
```

The original transaction dataset contained:
**1,005,000 records**
along with source-system information and ingestion metadata.
The purpose of this layer is to establish the incoming data structure before applying the deeper transformation logic.
The raw source should remain traceable, so downstream cleaning does not destroy the original state of the data.

---

# 5. Bronze Layer — Raw Data + Profiling

The Bronze layer stores the incoming datasets as Delta tables.

```
```

```
bronze.customers
bronze.accounts
bronze.transactions
bronze.merchants
bronze.branches
bronze.aml_alerts
```

A separate data-quality profile was also created:

```
```

```
bronze.data_quality_profile
```

The Bronze layer was intentionally kept close to the source rather than performing aggressive transformations.
This gives the pipeline a stable raw-data boundary and makes it possible to investigate where a downstream issue originated.
For example, the Bronze transaction table retained:

- Original transaction identifiers
- Customer and account references
- Merchant references
- Transaction type
- Channel
- Amount
- Currency
- Status
- Source system
- Ingestion timestamp

This separation between **raw ingestion** and **cleaned business data** became important later when validating the Silver and Gold layers.

---

# 6. Silver Layer — Cleaning, Standardization & Validation

The Silver layer is where most of the data-quality work happens.
The main objective was:

> **Take inconsistent source data and establish a trustworthy record for each business entity.**

The transformations included:

- String normalization
- `TRIM` / `UPPER`
- Data-type conversion
- Timestamp standardization
- Duplicate detection
- Deduplication
- Domain validation
- Relationship validation
- Business-key validation

### Timestamp standardization

The source contained different timestamp formats.
Instead of assuming one format, multiple parsing patterns were handled during transformation.
This allowed timestamps from different source representations to be converted into a consistent type before downstream analytics.

### Deduplication

Window functions were used to identify duplicate business keys and select the appropriate record.
For example, transaction records were partitioned by `transaction_id` and ordered using the defined record-selection logic.
The result:

```
```

```
Raw transactions        1,005,000
        ↓
Duplicate detection
        ↓
Unique transactions     1,000,000
```

The same principle was applied to the other datasets.

### Final Silver counts

```
```

```
Customers       50,000
Accounts        75,000
Transactions  1,000,000
Merchants       10,000
Branches           500
AML Alerts      20,000
```

At this stage, the data was ready to support business-level modeling.

---

# 7. Gold Layer — Business-Oriented Data Models

The Gold layer is where the cleaned data starts becoming useful from a business perspective.
Instead of exposing the raw relational structure directly to analysts, the data was reorganized into models designed around common financial analysis requirements.
Five Gold datasets were created.

| Gold DatasetGrain / Purpose |                            |
| --------------------------- | -------------------------- |
| `customer_360`              | One record per customer    |
| `transaction_analytics`     | One record per transaction |
| `aml_risk`                  | One record per AML alert   |
| `account_analytics`         | One record per account     |
| `branch_performance`        | One record per branch      |

---

## Customer 360

`gold.customer_360` provides a consolidated customer-level view.
It combines customer information with account and transaction metrics.
Examples include:

- Customer segment
- Risk rating
- KYC status
- Total accounts
- Active accounts
- Total transactions
- Successful transactions
- Total transaction amount
- Average transaction amount

The final dataset contains:
**50,000 unique customers.**
This model makes customer-level analysis possible without repeatedly rebuilding the same joins and aggregations.

---

## Transaction Analytics

`gold.transaction_analytics` provides a transaction-level analytical dataset.
Transaction information is enriched with:

- Customer information
- Account information
- Merchant information

Additional flags were created for analytical and data-quality purposes:

```
```

```
is_successful
is_negative_amount
is_unmapped_merchant
```

This allowed the analytics layer to answer questions about both **financial activity** and **data quality**.

---

## AML Risk

`gold.aml_risk` connects AML alerts with the related financial entities.
The model includes information that can be used to analyze:

- Alert severity
- Alert status
- High-priority alerts
- High-risk customers
- Related transactions
- Related accounts
- Merchant information

The final dataset contains:
**20,000 unique AML alerts.**

---

## Account Analytics

`gold.account_analytics` provides account-level metrics such as:

- Account type
- Customer
- Branch
- Currency
- Account status
- Credit limit
- Transaction count
- Successful transactions
- Failed transactions
- Reversed transactions
- Pending transactions
- Successful transaction amount
- Average successful transaction amount
- Last transaction timestamp

This creates a useful bridge between customer-level and transaction-level analysis.

---

## Branch Performance

`gold.branch_performance` aggregates account and transaction activity at the branch level.
This allows the pipeline to support analysis of branch-level:

- Account volume
- Transaction activity
- Transaction value
- Performance metrics

---

# 8. Data Quality Results

After the Silver and Gold transformations, validation checks were performed against the final datasets.

### Transaction validation

| CheckResult               |           |
| ------------------------- | --------- |
| Total transactions        | 1,000,000 |
| Unique transaction IDs    | 1,000,000 |
| Null transaction IDs      | 0         |
| Null customer IDs         | 0         |
| Null account IDs          | 0         |
| Duplicate transaction IDs | 0         |
| Null transaction amounts  | 2,488     |
| Negative amounts          | 245       |
| Unmapped merchants        | 2,502     |

The key identifiers were brought to zero duplicate/null violations.
Not every issue was removed.
That distinction matters.
**A data pipeline should not automatically delete every imperfect record. It should distinguish between a record that is invalid for processing and a record that is valid but contains a data-quality issue.**

---

# 9. Transaction Analysis

The final transaction dataset contains:

| StatusTransactions |               |
| ------------------ | ------------- |
| SUCCESS            | 909,985       |
| FAILED             | 49,993        |
| PENDING            | 20,039        |
| REVERSED           | 19,983        |
| **Total**          | **1,000,000** |

This allowed the project to move beyond pipeline construction into actual business analysis.
Transaction activity was also analyzed by transaction type.

| Transaction TypeTransactions |         |
| ---------------------------- | ------- |
| CARD_PURCHASE                | 379,783 |
| BANK_TRANSFER                | 200,425 |
| UPI                          | 179,254 |
| ATM_WITHDRAWAL               | 80,197  |
| BILL_PAYMENT                 | 70,043  |
| CASH_DEPOSIT                 | 50,185  |
| CHEQUE                       | 40,113  |

Successful transaction amounts were also calculated for each transaction type.
For example:

- Card purchases generated approximately **₹1.08B** in successful transaction value.
- ATM withdrawals generated approximately **₹1.11B**.
- Cash deposits generated approximately **₹746M**.
- Bank transfers generated approximately **₹570M**.
- UPI generated approximately **₹509M**.

These metrics were calculated from the Gold transaction model rather than directly from the raw source.

---

# 10. Customer Analysis

Customer-level analysis was performed using `gold.customer_360`.
The analysis looked at:

- Customer segment
- Risk rating
- Transaction frequency
- Total transaction value
- Average transaction value

One useful distinction from the analysis was that a customer's total transaction value could be driven by either:
**high transaction frequency**
or
**high average transaction value.**
For example, the top-value customer results contained both patterns.
A customer with fewer transactions but a very high average transaction amount can appear alongside a customer with many smaller transactions.
This is why both:

```
```

```
total_transaction_amount
```

and

```
```

```
average_transaction_amount
```

were retained in the Gold customer model.

---

# 11. Merchant Analysis

Merchant categories were also analyzed using the transaction data.
The dataset contained categories including:

- Restaurant
- Healthcare
- Utilities
- E-commerce
- Jewellery
- Travel
- Education
- Grocery
- Fuel
- Electronics

Transaction volumes were relatively distributed across these categories, allowing category-level transaction volume and successful transaction value to be compared.
This analysis demonstrates how the same Gold transaction model can support different business questions without rebuilding the underlying pipeline.

---

# 12. Data Quality Impact on Analytics

One of the more important parts of the project was not simply finding data-quality problems, but measuring their impact.
For example:

```
```

```
Mapped merchant transactions
997,498

Unmapped merchant transactions
2,502
```

The unmapped transactions represented approximately:
**0.25% of all transactions.**
The unmapped records contained approximately:
**₹11.94M total transaction value**
including approximately:
**₹10.75M successful transaction value.**
This means that simply dropping the unmapped transactions would not only hide a data-quality problem but would also remove legitimate financial activity from the analytical dataset.
The solution was therefore to preserve the transactions and expose the mapping issue through:

```
```

```
is_unmapped_merchant
```

---

# 13. Engineering Beyond ETL

The project also includes engineering concepts beyond the basic Bronze → Silver → Gold transformations.

### Incremental Processing

An incremental-processing demonstration was implemented to identify records belonging to batches that had not already been processed.
A control table was used to track processed batches.
The important distinction here was:

```
```

```
Incremental processing
        ↓
Determines WHAT needs processing

MERGE / Upsert
        ↓
Determines HOW changes are applied
```

These are related concepts but solve different problems.

---

## Delta MERGE

A Delta `MERGE` demonstration was implemented using an incoming customer dataset.
The scenario included:

- An existing customer with updated information
- A new customer

The `MERGE` operation handled:

```
```

```
MATCHED     → UPDATE
NOT MATCHED → INSERT
```

A duplicate incoming-record scenario was also tested using window-function deduplication before applying the merge.
This helped demonstrate why an incoming dataset should have one deterministic record per merge key before performing an upsert.

---

# 14. Data Quality Gates

A data-quality gate was created around critical transaction checks.
The validation included:

```
```

```
Total records
Null transaction IDs
Null customer IDs
Null account IDs
Invalid status values
Null amounts
Duplicate transaction IDs
```

The project distinguishes between:

### Critical failures

Examples:

- Null transaction ID
- Duplicate transaction ID
- Invalid status

These should prevent the dataset from being considered valid.

### Warnings

Example:

- Null transaction amount

A null amount may require investigation but does not automatically mean that the entire transaction record should be rejected.
A failing test dataset was also created containing an invalid transaction ID and invalid status.
The gate detected the failures and separated invalid records into a quarantine dataset with a rejection reason.

---

# 15. Workflow Orchestration

The complete pipeline was orchestrated using **Databricks Jobs**.
The production workflow is:

```
```

```
level_0_ingestion
        ↓
bronze_processing
        ↓
silver_processing
        ↓
gold_processing
        ↓
analytics_processing
```

Each task depends on the successful completion of the previous stage.
This turns the project from a collection of notebooks into an actual pipeline workflow.
The job was executed successfully from ingestion through analytics.

---

# 16. Performance Considerations

Performance was also considered while designing the Spark/Delta pipeline.
The project explored concepts including:

- Filtering early
- Selecting only required columns
- Reducing unnecessary shuffles
- Broadcast joins for small datasets
- Partition sizing
- Small-file considerations
- Delta `OPTIMIZE`
- Data skipping
- Adaptive Query Execution
- Data skew

The general principle used was:

```
```

```
Read less
   ↓
Move less data
   ↓
Shuffle less
   ↓
Compute less
   ↓
Write efficiently
```

These considerations become increasingly important as the same pipeline pattern scales from millions to much larger datasets.

---

# 17. Technology Stack

| TechnologyRole  |                                               |
| --------------- | --------------------------------------------- |
| Databricks      | Development and execution platform            |
| Apache Spark    | Distributed processing                        |
| Delta Lake      | Reliable storage and transactional operations |
| SQL             | Transformation, validation and analytics      |
| Unity Catalog   | Catalog and data organization                 |
| Databricks Jobs | Pipeline orchestration                        |
| Git             | Version control                               |
| GitHub          | Source-code repository                        |

---

# 18. Repository Structure

```
```

```
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

---

# 19. What This Project Demonstrates

FinFlow was built to demonstrate the complete workflow of a practical batch data engineering project:

```
```

```
Source Data
    ↓
Ingestion
    ↓
Raw Storage
    ↓
Data Profiling
    ↓
Cleaning
    ↓
Deduplication
    ↓
Validation
    ↓
Business Modeling
    ↓
Analytics
    ↓
Data Quality Monitoring
    ↓
Incremental Processing
    ↓
Upsert / MERGE
    ↓
Workflow Orchestration
```

The main focus was not simply creating tables.
The project was designed around questions such as:

- What happens when the source contains duplicates?
- What happens when duplicate records conflict?
- Should missing financial values be converted to zero?
- What happens when a foreign-key relationship is missing?
- Should invalid records be deleted or quarantined?
- How can already-processed batches be identified?
- How can new and existing records be handled with `MERGE`?
- How should individual pipeline stages depend on one another?
- How can data-quality problems be measured rather than hidden?

These decisions form the main engineering component of FinFlow.

---

# Project Scope

FinFlow uses synthetic financial data and is intended as a portfolio implementation of data engineering concepts.
It is **not a production banking system**, and the financial values do not represent real customer transactions.
The project focuses on demonstrating practical experience with:
**Databricks · Spark · Delta Lake · SQL · Data Quality · Data Modeling · Incremental Processing · MERGE · Workflow Orchestration · Financial Analytics**
