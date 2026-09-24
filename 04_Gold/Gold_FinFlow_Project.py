# Databricks notebook source
# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC LIMIT 5;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC LIMIT 5;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC LIMIT 5;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(DISTINCT account_id) AS total_accounts,
# MAGIC     COUNT(DISTINCT CASE
# MAGIC         WHEN status = 'ACTIVE' THEN account_id
# MAGIC     END) AS active_accounts
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC GROUP BY customer_id
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC
# MAGIC     COUNT(DISTINCT transaction_id) AS total_transactions,
# MAGIC
# MAGIC     COUNT(DISTINCT CASE
# MAGIC         WHEN status = 'SUCCESS' THEN transaction_id
# MAGIC     END) AS successful_transactions,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN status = 'SUCCESS' THEN amount
# MAGIC         ELSE 0
# MAGIC     END) AS total_transaction_amount,
# MAGIC
# MAGIC     AVG(CASE
# MAGIC         WHEN status = 'SUCCESS' THEN amount
# MAGIC     END) AS average_transaction_amount
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC GROUP BY customer_id
# MAGIC LIMIT 20;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC gold.customer_360# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create the Customer 360 Gold table# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.gold.customer_360
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC WITH account_metrics AS (
# MAGIC     SELECT
# MAGIC         customer_id,
# MAGIC         COUNT(DISTINCT account_id) AS total_accounts,
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'ACTIVE' THEN account_id
# MAGIC         END) AS active_accounts
# MAGIC     FROM Finflow_Project_catalog.silver.accounts
# MAGIC     GROUP BY customer_id
# MAGIC ),
# MAGIC
# MAGIC transaction_metrics AS (
# MAGIC     SELECT
# MAGIC         customer_id,
# MAGIC         COUNT(DISTINCT transaction_id) AS total_transactions,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'SUCCESS' THEN transaction_id
# MAGIC         END) AS successful_transactions,
# MAGIC
# MAGIC         SUM(CASE
# MAGIC             WHEN status = 'SUCCESS' THEN amount
# MAGIC             ELSE 0
# MAGIC         END) AS total_transaction_amount,
# MAGIC
# MAGIC         AVG(CASE
# MAGIC             WHEN status = 'SUCCESS' THEN amount
# MAGIC         END) AS average_transaction_amount
# MAGIC
# MAGIC     FROM Finflow_Project_catalog.silver.transactions
# MAGIC     GROUP BY customer_id
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     c.customer_id,
# MAGIC     c.first_name,
# MAGIC     c.last_name,
# MAGIC     c.gender,
# MAGIC     c.date_of_birth,
# MAGIC     c.city,
# MAGIC     c.state,
# MAGIC     c.country,
# MAGIC     c.kyc_status,
# MAGIC     c.risk_rating,
# MAGIC     c.customer_segment,
# MAGIC
# MAGIC     COALESCE(am.total_accounts, 0) AS total_accounts,
# MAGIC     COALESCE(am.active_accounts, 0) AS active_accounts,
# MAGIC
# MAGIC     COALESCE(tm.total_transactions, 0) AS total_transactions,
# MAGIC     COALESCE(tm.successful_transactions, 0) AS successful_transactions,
# MAGIC     COALESCE(tm.total_transaction_amount, 0) AS total_transaction_amount,
# MAGIC     tm.average_transaction_amount
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.customers c
# MAGIC
# MAGIC LEFT JOIN account_metrics am
# MAGIC     ON c.customer_id = am.customer_id
# MAGIC
# MAGIC LEFT JOIN transaction_metrics tm
# MAGIC     ON c.customer_id = tm.customer_id;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     COUNT(DISTINCT customer_id) AS unique_customers
# MAGIC FROM Finflow_Project_catalog.gold.customer_360;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC DESCRIBE Finflow_Project_catalog.gold.customer_360;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC After the Silver layer is corrected and Gold is rebuilt, the expected Customer 360 grain is: ```text
# MAGIC total_rows = 50000
# MAGIC unique_customers = 50000
# MAGIC ```
# MAGIC
# MAGIC is exactly what we wanted for `gold.customer_360`.
# MAGIC
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # 🟡 GOLD — Phase 1: Customer 360
# MAGIC
# MAGIC Customer 360 is validated at a one-row-per-customer grain before downstream use.
# MAGIC
# MAGIC ### Grain
# MAGIC
# MAGIC One row = **one customer**
# MAGIC
# MAGIC ```text
# MAGIC customer_360
# MAGIC         │
# MAGIC         └── customer_id = unique
# MAGIC ```
# MAGIC
# MAGIC And it currently combines:
# MAGIC
# MAGIC ```text
# MAGIC Customer information
# MAGIC         +
# MAGIC Account metrics
# MAGIC         +
# MAGIC Transaction metrics
# MAGIC ```
# MAGIC
# MAGIC That's a legitimate Gold business mart.
# MAGIC
# MAGIC But we're going to make Gold a little more industry-like rather than stopping at basic counts.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 1️⃣ First: inspect what we currently have
# MAGIC
# MAGIC Run:
# MAGIC
# MAGIC ```sql
# MAGIC %sql
# MAGIC
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC LIMIT 10;
# MAGIC ```
# MAGIC
# MAGIC Then run this:
# MAGIC
# MAGIC ```sql
# MAGIC %sql
# MAGIC
# MAGIC DESCRIBE Finflow_Project_catalog.gold.customer_360;
# MAGIC ```
# MAGIC
# MAGIC These are **two quick checks**, not another giant profiling exercise.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # 2️⃣ Then we're going to add business metrics
# MAGIC
# MAGIC Our current Customer 360 has:
# MAGIC
# MAGIC ```text
# MAGIC customer_id
# MAGIC first_name
# MAGIC last_name
# MAGIC gender
# MAGIC date_of_birth
# MAGIC city
# MAGIC state
# MAGIC country
# MAGIC kyc_status
# MAGIC risk_rating
# MAGIC customer_segment
# MAGIC
# MAGIC total_accounts
# MAGIC active_accounts
# MAGIC
# MAGIC total_transactions
# MAGIC successful_transactions
# MAGIC total_transaction_amount
# MAGIC average_transaction_amount
# MAGIC ```
# MAGIC
# MAGIC That's good, but a bank/business analyst would immediately want things like:
# MAGIC
# MAGIC ### Transaction success rate
# MAGIC
# MAGIC ```text
# MAGIC successful_transactions
# MAGIC ──────────────────────── × 100
# MAGIC total_transactions
# MAGIC ```
# MAGIC
# MAGIC ### Account activity rate
# MAGIC
# MAGIC ```text
# MAGIC active_accounts
# MAGIC ─────────────── × 100
# MAGIC total_accounts
# MAGIC ```
# MAGIC
# MAGIC ### Customer transaction status
# MAGIC
# MAGIC For example:
# MAGIC
# MAGIC ```text
# MAGIC HIGH_ACTIVITY
# MAGIC MEDIUM_ACTIVITY
# MAGIC LOW_ACTIVITY
# MAGIC ```
# MAGIC
# MAGIC based on transaction volume.
# MAGIC
# MAGIC ### Customer value
# MAGIC
# MAGIC We can derive a business classification from transaction activity, e.g.:
# MAGIC
# MAGIC ```text
# MAGIC HIGH_VALUE
# MAGIC MEDIUM_VALUE
# MAGIC LOW_VALUE
# MAGIC ```
# MAGIC
# MAGIC But **we need to define these thresholds explicitly** rather than inventing arbitrary "banking truth."
# MAGIC
# MAGIC For the project, we'll document them as **project-defined analytical rules**.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # 3️⃣ One important thing before we modify it
# MAGIC
# MAGIC There is one issue from our Silver validation:
# MAGIC
# MAGIC ```text
# MAGIC transactions → merchants
# MAGIC 2513 orphan references
# MAGIC ```
# MAGIC
# MAGIC We intentionally kept those transactions because deleting financial transactions would be bad practice.
# MAGIC
# MAGIC That means our Gold transaction analytics should **not accidentally lose those transactions through an INNER JOIN to merchants.**
# MAGIC
# MAGIC We'll use:
# MAGIC
# MAGIC ```text
# MAGIC LEFT JOIN
# MAGIC ```
# MAGIC
# MAGIC when merchant enrichment is needed.
# MAGIC
# MAGIC This is actually a nice interview point:
# MAGIC
# MAGIC > "I preserved transactions with unresolved merchant references rather than dropping them, and used left joins in downstream analytics so incomplete dimension data wouldn't cause fact loss."
# MAGIC
# MAGIC This preserves the transaction grain while retaining visibility into missing enrichment data.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # Our Gold roadmap from here
# MAGIC
# MAGIC We're going to build this in **three batches**, not one table at a time:
# MAGIC
# MAGIC ### 🟡 Batch 1 — Customer & Transaction analytics
# MAGIC
# MAGIC ```text
# MAGIC gold.customer_360          ✅ already created
# MAGIC gold.transaction_analytics
# MAGIC ```
# MAGIC
# MAGIC ### 🟠 Batch 2 — Risk & account analytics
# MAGIC
# MAGIC ```text
# MAGIC gold.aml_risk
# MAGIC gold.account_analytics
# MAGIC ```
# MAGIC
# MAGIC ### 🟢 Batch 3 — Branch & business performance
# MAGIC
# MAGIC ```text
# MAGIC gold.branch_performance
# MAGIC ```
# MAGIC
# MAGIC Then:
# MAGIC
# MAGIC ```text
# MAGIC Gold
# MAGIC  ↓
# MAGIC Analytics / dashboards
# MAGIC  ↓
# MAGIC KPIs
# MAGIC  ↓
# MAGIC Interview explanation
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### So right now:
# MAGIC
# MAGIC Run only these two quick queries:
# MAGIC
# MAGIC ```sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC LIMIT 10;
# MAGIC ```
# MAGIC
# MAGIC and
# MAGIC
# MAGIC ```sql
# MAGIC DESCRIBE Finflow_Project_catalog.gold.customer_360;
# MAGIC ```
# MAGIC
# MAGIC **Send me the output.**
# MAGIC
# MAGIC Then I'll give you **Customer 360 enhancement + Transaction Analytics together**, so we're moving at the pace you wanted. 🚀# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Gold Batch 1 — Transaction Analytics# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.gold.transaction_analytics
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     t.transaction_id,
# MAGIC     t.transaction_timestamp,
# MAGIC
# MAGIC     -- Customer
# MAGIC     t.customer_id,
# MAGIC     CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
# MAGIC     c.customer_segment,
# MAGIC     c.risk_rating AS customer_risk_rating,
# MAGIC     c.city AS customer_city,
# MAGIC     c.state AS customer_state,
# MAGIC
# MAGIC     -- Account
# MAGIC     t.account_id,
# MAGIC     a.account_type,
# MAGIC     a.status AS account_status,
# MAGIC
# MAGIC     -- Merchant
# MAGIC     t.merchant_id,
# MAGIC     m.merchant_name,
# MAGIC     m.merchant_category,
# MAGIC     m.risk_rating AS merchant_risk_rating,
# MAGIC
# MAGIC     -- Transaction
# MAGIC     t.transaction_type,
# MAGIC     t.channel,
# MAGIC     t.amount,
# MAGIC     t.currency,
# MAGIC     t.status AS transaction_status,
# MAGIC     t.source_system,
# MAGIC
# MAGIC     -- Business flags
# MAGIC     CASE
# MAGIC         WHEN t.status = 'SUCCESS' THEN 1
# MAGIC         ELSE 0
# MAGIC     END AS is_successful,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN t.amount < 0 THEN 1
# MAGIC         ELSE 0
# MAGIC     END AS is_negative_amount,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN m.merchant_id IS NULL
# MAGIC              AND t.merchant_id IS NOT NULL
# MAGIC         THEN 1
# MAGIC         ELSE 0
# MAGIC     END AS is_unmapped_merchant
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON t.customer_id = c.customer_id
# MAGIC
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.accounts a
# MAGIC     ON t.account_id = a.account_id
# MAGIC
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.merchants m
# MAGIC     ON t.merchant_id = m.merchant_id;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Why LEFT JOIN is used
# MAGIC
# MAGIC This is actually an important interview point.
# MAGIC
# MAGIC We already discovered 2,513 transactions whose non-null merchant_id doesn't exist in the merchant master.
# MAGIC
# MAGIC We don't want those transactions to disappear.
# MAGIC
# MAGIC So:
# MAGIC
# MAGIC Transactions
# MAGIC      │
# MAGIC      ├── Customer → LEFT JOIN
# MAGIC      ├── Account  → LEFT JOIN
# MAGIC      └── Merchant → LEFT JOIN
# MAGIC
# MAGIC The transaction remains in Gold even if enrichment data is missing.
# MAGIC
# MAGIC And our:
# MAGIC
# MAGIC is_unmapped_merchant
# MAGIC
# MAGIC flag makes that data-quality problem visible rather than hiding it.
# MAGIC
# MAGIC 🔍 Then validate it
# MAGIC
# MAGIC Run these 4 checks together:# COMMAND ----------

# MAGIC %sql
# MAGIC -- 1. Row count and transaction grain
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     COUNT(DISTINCT transaction_id) AS unique_transactions
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 2. Transaction status distribution
# MAGIC SELECT
# MAGIC     transaction_status,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(amount) AS total_amount
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY transaction_status
# MAGIC ORDER BY transaction_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 3. Unmapped merchants
# MAGIC SELECT
# MAGIC     is_unmapped_merchant,
# MAGIC     COUNT(*) AS transaction_count
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY is_unmapped_merchant;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 4. Inspect the final Gold data
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC gold.aml_risk and gold.account_analytics# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC 1. gold.aml_risk
# MAGIC
# MAGIC AML = Anti-Money Laundering.
# MAGIC
# MAGIC Grain:
# MAGIC
# MAGIC 1 row = 1 AML alert
# MAGIC
# MAGIC We'll connect alerts to transactions and customers so an analyst/investigator can actually understand the alert.
# MAGIC
# MAGIC 2. gold.account_analytics
# MAGIC
# MAGIC Grain:
# MAGIC
# MAGIC 1 row = 1 account
# MAGIC
# MAGIC This will give us account-level transaction behavior.# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create gold.aml_risk# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.gold.aml_risk
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     al.alert_id,
# MAGIC     al.alert_timestamp,
# MAGIC     al.alert_type,
# MAGIC     al.severity,
# MAGIC     al.case_status,
# MAGIC     al.investigator,
# MAGIC
# MAGIC     -- Customer
# MAGIC     al.customer_id,
# MAGIC     CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
# MAGIC     c.customer_segment,
# MAGIC     c.risk_rating AS customer_risk_rating,
# MAGIC     c.kyc_status,
# MAGIC     c.city,
# MAGIC     c.state,
# MAGIC
# MAGIC     -- Transaction
# MAGIC     al.transaction_id,
# MAGIC     t.transaction_timestamp,
# MAGIC     t.amount AS transaction_amount,
# MAGIC     t.currency,
# MAGIC     t.transaction_type,
# MAGIC     t.channel,
# MAGIC     t.status AS transaction_status,
# MAGIC
# MAGIC     -- Account
# MAGIC     t.account_id,
# MAGIC     a.account_type,
# MAGIC     a.status AS account_status,
# MAGIC
# MAGIC     -- Merchant
# MAGIC     t.merchant_id,
# MAGIC     m.merchant_name,
# MAGIC     m.merchant_category,
# MAGIC     m.risk_rating AS merchant_risk_rating,
# MAGIC
# MAGIC     -- Business indicators
# MAGIC     CASE
# MAGIC         WHEN al.severity IN ('HIGH', 'CRITICAL') THEN 1
# MAGIC         ELSE 0
# MAGIC     END AS is_high_priority,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN c.risk_rating IN ('HIGH', 'CRITICAL')
# MAGIC              OR m.risk_rating IN ('HIGH', 'CRITICAL')
# MAGIC         THEN 1
# MAGIC         ELSE 0
# MAGIC     END AS involves_high_risk_party
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts al
# MAGIC
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.transactions t
# MAGIC     ON al.transaction_id = t.transaction_id
# MAGIC
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON al.customer_id = c.customer_id
# MAGIC
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.accounts a
# MAGIC     ON t.account_id = a.account_id
# MAGIC
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.merchants m
# MAGIC     ON t.merchant_id = m.merchant_id;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create gold.account_analytics# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.gold.account_analytics
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH transaction_metrics AS (
# MAGIC     SELECT
# MAGIC         account_id,
# MAGIC
# MAGIC         COUNT(DISTINCT transaction_id) AS total_transactions,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'SUCCESS'
# MAGIC             THEN transaction_id
# MAGIC         END) AS successful_transactions,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'FAILED'
# MAGIC             THEN transaction_id
# MAGIC         END) AS failed_transactions,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'REVERSED'
# MAGIC             THEN transaction_id
# MAGIC         END) AS reversed_transactions,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'PENDING'
# MAGIC             THEN transaction_id
# MAGIC         END) AS pending_transactions,
# MAGIC
# MAGIC         SUM(CASE
# MAGIC             WHEN status = 'SUCCESS'
# MAGIC             THEN amount
# MAGIC             ELSE 0
# MAGIC         END) AS successful_transaction_amount,
# MAGIC
# MAGIC         AVG(CASE
# MAGIC             WHEN status = 'SUCCESS'
# MAGIC             THEN amount
# MAGIC         END) AS average_successful_transaction_amount,
# MAGIC
# MAGIC         MAX(transaction_timestamp) AS last_transaction_timestamp
# MAGIC
# MAGIC     FROM Finflow_Project_catalog.silver.transactions
# MAGIC     GROUP BY account_id
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     a.account_id,
# MAGIC     a.customer_id,
# MAGIC     a.account_type,
# MAGIC     a.branch_id,
# MAGIC     a.currency,
# MAGIC     a.opening_date,
# MAGIC     a.status AS account_status,
# MAGIC     a.credit_limit,
# MAGIC
# MAGIC     COALESCE(tm.total_transactions, 0) AS total_transactions,
# MAGIC     COALESCE(tm.successful_transactions, 0) AS successful_transactions,
# MAGIC     COALESCE(tm.failed_transactions, 0) AS failed_transactions,
# MAGIC     COALESCE(tm.reversed_transactions, 0) AS reversed_transactions,
# MAGIC     COALESCE(tm.pending_transactions, 0) AS pending_transactions,
# MAGIC     COALESCE(tm.successful_transaction_amount, 0) AS successful_transaction_amount,
# MAGIC     tm.average_successful_transaction_amount,
# MAGIC     tm.last_transaction_timestamp
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.accounts a
# MAGIC
# MAGIC LEFT JOIN transaction_metrics tm
# MAGIC     ON a.account_id = tm.account_id;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     COUNT(DISTINCT alert_id) AS unique_alerts
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     severity,
# MAGIC     case_status,
# MAGIC     COUNT(*) AS alert_count
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC GROUP BY severity, case_status
# MAGIC ORDER BY severity, case_status;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     COUNT(DISTINCT account_id) AS unique_accounts
# MAGIC FROM Finflow_Project_catalog.gold.account_analytics;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     account_status,
# MAGIC     COUNT(*) AS account_count,
# MAGIC     SUM(successful_transaction_amount) AS transaction_value
# MAGIC FROM Finflow_Project_catalog.gold.account_analytics
# MAGIC GROUP BY account_status;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.gold.account_analytics
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC aml_risk has some case_status = NULL:
# MAGIC
# MAGIC CRITICAL: 4
# MAGIC HIGH: 16
# MAGIC MEDIUM: 36
# MAGIC LOW: 42
# MAGIC
# MAGIC That's 98 alerts with missing case status. Don't "fix" them by guessing a status. This is exactly the kind of issue an enterprise pipeline should preserve/flag.
# MAGIC
# MAGIC Also, UNASSIGNED investigators are present, which is a realistic operational condition.# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Gold Batch 3 — Branch Performance# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.gold.branch_performance
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH account_metrics AS (
# MAGIC     SELECT
# MAGIC         branch_id,
# MAGIC
# MAGIC         COUNT(DISTINCT account_id) AS total_accounts,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'ACTIVE'
# MAGIC             THEN account_id
# MAGIC         END) AS active_accounts,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN status = 'CLOSED'
# MAGIC             THEN account_id
# MAGIC         END) AS closed_accounts
# MAGIC
# MAGIC     FROM Finflow_Project_catalog.silver.accounts
# MAGIC     GROUP BY branch_id
# MAGIC ),
# MAGIC
# MAGIC transaction_metrics AS (
# MAGIC     SELECT
# MAGIC         a.branch_id,
# MAGIC
# MAGIC         COUNT(DISTINCT t.transaction_id) AS total_transactions,
# MAGIC
# MAGIC         COUNT(DISTINCT CASE
# MAGIC             WHEN t.status = 'SUCCESS'
# MAGIC             THEN t.transaction_id
# MAGIC         END) AS successful_transactions,
# MAGIC
# MAGIC         SUM(CASE
# MAGIC             WHEN t.status = 'SUCCESS'
# MAGIC             THEN t.amount
# MAGIC             ELSE 0
# MAGIC         END) AS successful_transaction_amount,
# MAGIC
# MAGIC         AVG(CASE
# MAGIC             WHEN t.status = 'SUCCESS'
# MAGIC             THEN t.amount
# MAGIC         END) AS average_successful_transaction_amount
# MAGIC
# MAGIC     FROM Finflow_Project_catalog.silver.transactions t
# MAGIC
# MAGIC     INNER JOIN Finflow_Project_catalog.silver.accounts a
# MAGIC         ON t.account_id = a.account_id
# MAGIC
# MAGIC     GROUP BY a.branch_id
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     b.branch_id,
# MAGIC     b.branch_name,
# MAGIC     b.city,
# MAGIC     b.state,
# MAGIC     b.branch_type,
# MAGIC
# MAGIC     COALESCE(am.total_accounts, 0) AS total_accounts,
# MAGIC     COALESCE(am.active_accounts, 0) AS active_accounts,
# MAGIC     COALESCE(am.closed_accounts, 0) AS closed_accounts,
# MAGIC
# MAGIC     COALESCE(tm.total_transactions, 0) AS total_transactions,
# MAGIC     COALESCE(tm.successful_transactions, 0) AS successful_transactions,
# MAGIC     COALESCE(tm.successful_transaction_amount, 0) AS successful_transaction_amount,
# MAGIC     tm.average_successful_transaction_amount
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.branches b
# MAGIC
# MAGIC LEFT JOIN account_metrics am
# MAGIC     ON b.branch_id = am.branch_id
# MAGIC
# MAGIC LEFT JOIN transaction_metrics tm
# MAGIC     ON b.branch_id = tm.branch_id;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Branch grain# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     COUNT(DISTINCT branch_id) AS unique_branches
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Branch performance# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     branch_id,
# MAGIC     branch_name,
# MAGIC     city,
# MAGIC     state,
# MAGIC     total_accounts,
# MAGIC     active_accounts,
# MAGIC     total_transactions,
# MAGIC     successful_transactions,
# MAGIC     successful_transaction_amount
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance
# MAGIC ORDER BY successful_transaction_amount DESC
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Check for accidental multiplication# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     COUNT(DISTINCT branch_id) AS unique_branches
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance
# MAGIC WHERE branch_id IS NOT NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Inspect the table# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC SOURCE FILES
# MAGIC      ↓
# MAGIC LEVEL 0
# MAGIC      ↓
# MAGIC BRONZE
# MAGIC   ├── customers
# MAGIC   ├── accounts
# MAGIC   ├── transactions
# MAGIC   ├── merchants
# MAGIC   ├── branches
# MAGIC   ├── aml_alerts
# MAGIC   └── data_quality_profile
# MAGIC      ↓
# MAGIC SILVER
# MAGIC   ├── cleaned & standardized
# MAGIC   ├── deduplicated
# MAGIC   ├── validated
# MAGIC   └── relationship checks
# MAGIC      ↓
# MAGIC GOLD
# MAGIC   ├── customer_360          50K customers
# MAGIC   ├── transaction_analytics 1M transactions
# MAGIC   ├── aml_risk              20K alerts
# MAGIC   ├── account_analytics     75K accounts
# MAGIC   └── branch_performance    500 branches# COMMAND ----------# MAGIC %md
# MAGIC %md# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Grain + uniqueness audit# COMMAND ----------

# MAGIC %sql
# MAGIC -- GOLD GRAIN AUDIT
# MAGIC SELECT 'customer_360' AS table_name,
# MAGIC        COUNT(*) AS total_rows,
# MAGIC        COUNT(DISTINCT customer_id) AS unique_keys
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'transaction_analytics',
# MAGIC        COUNT(*),
# MAGIC        COUNT(DISTINCT transaction_id)
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'aml_risk',
# MAGIC        COUNT(*),
# MAGIC        COUNT(DISTINCT alert_id)
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'account_analytics',
# MAGIC        COUNT(*),
# MAGIC        COUNT(DISTINCT account_id)
# MAGIC FROM Finflow_Project_catalog.gold.account_analytics
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'branch_performance',
# MAGIC        COUNT(*),
# MAGIC        COUNT(DISTINCT branch_id)
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Important NULL audit# COMMAND ----------

# MAGIC %sql
# MAGIC -- CUSTOMER 360
# MAGIC SELECT
# MAGIC     'customer_360' AS table_name,
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
# MAGIC     SUM(CASE WHEN customer_segment IS NULL THEN 1 ELSE 0 END) AS null_segment,
# MAGIC     SUM(CASE WHEN risk_rating IS NULL THEN 1 ELSE 0 END) AS null_risk_rating
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC -- TRANSACTION ANALYTICS
# MAGIC SELECT
# MAGIC     'transaction_analytics',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC -- AML RISK
# MAGIC SELECT
# MAGIC     'aml_risk',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN alert_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC -- ACCOUNT ANALYTICS
# MAGIC SELECT
# MAGIC     'account_analytics',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.gold.account_analytics
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC -- BRANCH PERFORMANCE
# MAGIC SELECT
# MAGIC     'branch_performance',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN state IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Business metric sanity check# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_transactions,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_status = 'SUCCESS'
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS successful_transactions,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_status = 'FAILED'
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS failed_transactions,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_status = 'PENDING'
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS pending_transactions,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_status = 'REVERSED'
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS reversed_transactions,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN amount IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS null_amounts,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN amount < 0
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS negative_amounts
# MAGIC
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Relationship audit# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     'transactions_without_customer' AS check_name,
# MAGIC     COUNT(*) AS issue_count
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC WHERE customer_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'transactions_without_account',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC WHERE account_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'transactions_with_unmapped_merchant',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC WHERE is_unmapped_merchant = 1
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'aml_alerts_without_transaction',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC WHERE transaction_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'aml_alerts_without_customer',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC WHERE customer_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Gold table health summary# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     'Customers' AS metric,
# MAGIC     COUNT(*) AS value
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'Transactions',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'AML Alerts',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'Accounts',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.account_analytics
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'Branches',
# MAGIC     COUNT(*)
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC The Gold audit confirms the intended grain and highlights the remaining data-quality conditions that should be monitored.
# MAGIC
# MAGIC ## 🏁 FinFlow Gold Audit
# MAGIC
# MAGIC | Gold table              | Grain         | Key uniqueness | Important NULLs      | Status         |
# MAGIC | ----------------------- | ------------- | -------------- | -------------------- | -------------- |
# MAGIC | `customer_360`          | 1 customer    | ✅ 50K / 50K    | ✅ 0                  | ✅              |
# MAGIC | `transaction_analytics` | 1 transaction | ✅ 1M / 1M      | ✅ Customer/account 0 | ✅              |
# MAGIC | `aml_risk`              | 1 alert       | ✅ 20K / 20K    | ✅ 0                  | ✅              |
# MAGIC | `account_analytics`     | 1 account     | ✅ 75K / 75K    | ⚠️ 298 segments      | ⚠️ investigate |
# MAGIC | `branch_performance`    | 1 branch      | ✅ 500 / 500    | ✅ 0                  | ✅              |
# MAGIC
# MAGIC ### ⚠️ 1. The 298 `customer_segment` NULLs
# MAGIC
# MAGIC This is **not a Gold join failure**.
# MAGIC
# MAGIC Remember, `account_analytics` is built from:
# MAGIC
# MAGIC ```text
# MAGIC accounts → transaction_metrics → account_analytics
# MAGIC ```
# MAGIC
# MAGIC We never joined `customer_360` or the customer table into it, so `customer_segment` shouldn't actually be a column in the SQL we created.
# MAGIC
# MAGIC If your output says:
# MAGIC
# MAGIC ```text
# MAGIC account_analytics → null_segment = 298
# MAGIC ```
# MAGIC
# MAGIC then either:
# MAGIC
# MAGIC * the table was modified after creation, or
# MAGIC * the validation query is reading a different/older schema than the query we built.
# MAGIC
# MAGIC The audit identifies the condition directly rather than inferring a value.
# MAGIC
# MAGIC Run:
# MAGIC
# MAGIC ```sql
# MAGIC DESCRIBE Finflow_Project_catalog.gold.account_analytics;
# MAGIC ```
# MAGIC
# MAGIC That's the only thing I want to investigate here.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## ⚠️ 2. 2,502 unmapped merchants
# MAGIC
# MAGIC This one is **expected and useful**.
# MAGIC
# MAGIC ```text
# MAGIC 2,502 / 1,000,000
# MAGIC ```
# MAGIC
# MAGIC transactions have a non-null merchant ID that doesn't resolve to the merchant master.
# MAGIC
# MAGIC We deliberately preserved them using `LEFT JOIN`.
# MAGIC
# MAGIC That's actually a nice interview story:
# MAGIC
# MAGIC > "During Silver validation, we identified orphan merchant references. Rather than dropping potentially valid financial transactions, the Gold transaction fact retained them using a LEFT JOIN and exposed them through an `is_unmapped_merchant` data-quality flag."
# MAGIC
# MAGIC That's much better than quietly deleting 2,502 financial records.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## ⚠️ 3. 2,488 NULL amounts
# MAGIC
# MAGIC This deserves attention later.
# MAGIC
# MAGIC We have:
# MAGIC
# MAGIC ```text
# MAGIC 1,000,000 transactions
# MAGIC 2,488 NULL amounts
# MAGIC 245 negative amounts
# MAGIC ```
# MAGIC
# MAGIC Don't automatically replace NULL with `0`.
# MAGIC
# MAGIC For financial data:
# MAGIC
# MAGIC ```text
# MAGIC NULL ≠ 0
# MAGIC ```
# MAGIC
# MAGIC A NULL amount means **amount is unknown/missing**.
# MAGIC
# MAGIC Zero means **the transaction amount was explicitly zero**.
# MAGIC
# MAGIC We'll investigate this in the data-quality layer rather than corrupting the financial data.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## ⚠️ 4. 245 negative amounts
# MAGIC
# MAGIC Again, don't delete them.
# MAGIC
# MAGIC A negative transaction could represent things such as a reversal/refund/adjustment depending on the source's business rules.
# MAGIC
# MAGIC We'll inspect:
# MAGIC
# MAGIC ```text
# MAGIC transaction_type
# MAGIC status
# MAGIC amount
# MAGIC ```
# MAGIC
# MAGIC before deciding whether they're legitimate.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # 🟢 Overall verdict
# MAGIC
# MAGIC The core Gold architecture is **working**:
# MAGIC
# MAGIC ```text
# MAGIC                      FINFLOW
# MAGIC                         │
# MAGIC              ┌──────────┴──────────┐
# MAGIC              │                     │
# MAGIC           SILVER                 GOLD
# MAGIC              │                     │
# MAGIC       cleaned/validated      business-ready
# MAGIC                                    │
# MAGIC        ┌────────┬─────────┬────────┬─────────┐
# MAGIC        ↓        ↓         ↓        ↓         ↓
# MAGIC     Customer Transaction  AML    Account   Branch
# MAGIC       360    Analytics   Risk   Analytics Performance
# MAGIC ```
# MAGIC
# MAGIC And the numbers reconcile nicely:
# MAGIC
# MAGIC **50K customers → 75K accounts → 1M transactions → 20K AML alerts → 500 branches**
# MAGIC
# MAGIC That's a coherent financial-data ecosystem rather than five unrelated demo tables.
# MAGIC
# MAGIC ### So don't rebuild anything.
# MAGIC
# MAGIC **Next:** run only this:
# MAGIC
# MAGIC ```sql
# MAGIC DESCRIBE Finflow_Project_catalog.gold.account_analytics;
# MAGIC ```
# MAGIC
# MAGIC We'll resolve the 298 NULL-segment discrepancy, then I want to do a **small financial-data quality investigation** for the 2,488 NULL amounts + 245 negative amounts.
# MAGIC
# MAGIC After that, I'm comfortable saying:
# MAGIC
# MAGIC > 🟢 **FinFlow Core Bronze → Silver → Gold = COMPLETE**
# MAGIC
# MAGIC Then we move to the engineering layer that will matter heavily for your Data Engineer interviews. 🚀# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.gold.account_analytics;

# COMMAND ----------
