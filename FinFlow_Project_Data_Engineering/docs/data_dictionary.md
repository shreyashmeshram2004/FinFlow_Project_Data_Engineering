# FinFlow Data Dictionary — High-Level

## Bronze

| Table | Purpose |
|---|---|
| `bronze.customers` | Customer source data plus ingestion metadata |
| `bronze.accounts` | Account source data plus ingestion metadata |
| `bronze.transactions` | Transaction source data plus ingestion metadata |
| `bronze.merchants` | Merchant source data |
| `bronze.branches` | Branch source data |
| `bronze.aml_alerts` | AML alert source data |
| `bronze.data_quality_profile` | Initial profiling results |

## Silver

| Table | Purpose |
|---|---|
| `silver.customers` | Standardized and deduplicated customers |
| `silver.accounts` | Standardized and deduplicated accounts |
| `silver.transactions` | Standardized and deduplicated transactions |
| `silver.merchants` | Standardized and deduplicated merchants |
| `silver.branches` | Standardized and deduplicated branches |
| `silver.aml_alerts` | Standardized and deduplicated AML alerts |

## Gold

| Table | Business grain / purpose |
|---|---|
| `gold.customer_360` | One row per customer with account and transaction metrics |
| `gold.transaction_analytics` | One row per transaction with business context |
| `gold.aml_risk` | AML alert records enriched with related entities |
| `gold.account_analytics` | One row per account with transaction metrics |
| `gold.branch_performance` | One row per branch with account/transaction metrics |
