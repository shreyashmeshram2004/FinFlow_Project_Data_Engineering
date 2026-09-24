# MAGIC %md
# MAGIC %md
# MAGIC Engineering# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Topic 1: Incremental Processing
# MAGIC
# MAGIC
# MAGIC First, what are we trying to solve?
# MAGIC
# MAGIC Right now FinFlow has:
# MAGIC
# MAGIC 1,005,000 raw transactions
# MAGIC         ↓
# MAGIC Bronze
# MAGIC         ↓
# MAGIC Silver
# MAGIC         ↓
# MAGIC Gold
# MAGIC
# MAGIC Imagine tomorrow another 20,000 transactions arrive.
# MAGIC
# MAGIC A bad pipeline does:
# MAGIC
# MAGIC 1,025,000 records
# MAGIC ↓
# MAGIC process ALL again
# MAGIC
# MAGIC An incremental pipeline does:
# MAGIC
# MAGIC Existing: 1,005,000
# MAGIC New:         20,000
# MAGIC              ↓
# MAGIC       process only these
# MAGIC              ↓
# MAGIC Existing + new
# MAGIC = 1,025,000
# MAGIC
# MAGIC That's the fundamental idea.
# MAGIC
# MAGIC But there's a problem in our current FinFlow
# MAGIC
# MAGIC Your current Bronze transactions have:
# MAGIC
# MAGIC transaction_id
# MAGIC transaction_timestamp
# MAGIC customer_id
# MAGIC account_id
# MAGIC merchant_id
# MAGIC ...
# MAGIC ingestion_timestamp
# MAGIC
# MAGIC And currently all 1,005,000 records have the same ingestion_timestamp.
# MAGIC
# MAGIC So we cannot honestly pretend that your existing dataset contains multiple historical batches.
# MAGIC
# MAGIC Instead, we're going to create a small simulated new batch to demonstrate the engineering pattern properly.
# MAGIC
# MAGIC That's actually better than faking historical metadata.# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     ingestion_timestamp,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC GROUP BY ingestion_timestamp
# MAGIC ORDER BY ingestion_timestamp;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC For proper incremental processing, every incoming batch should have something that lets us distinguish:
# MAGIC
# MAGIC Batch 1 → existing data
# MAGIC Batch 2 → tomorrow's arrival
# MAGIC Batch 3 → next arrival
# MAGIC ...
# MAGIC
# MAGIC For our project, we'll use a simple batch_id concept.
# MAGIC
# MAGIC The production Bronze table is left unchanged; the incremental pattern is demonstrated with a separate controlled table.
# MAGIC
# MAGIC The existing ingestion metadata is inspected to determine whether a reliable batch identifier is available.# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     source_system,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC GROUP BY source_system
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 1 — Create a new incoming batch
# MAGIC
# MAGIC A controlled sample is used to simulate a new source arrival with a new ingestion timestamp and batch identifier.
# MAGIC
# MAGIC This is an engineering demonstration only; the sampled transaction IDs are not treated as genuinely new financial transactions.# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.transactions_incremental_demo
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     transaction_id,
# MAGIC     transaction_timestamp,
# MAGIC     customer_id,
# MAGIC     account_id,
# MAGIC     merchant_id,
# MAGIC     transaction_type,
# MAGIC     channel,
# MAGIC     amount,
# MAGIC     currency,
# MAGIC     status,
# MAGIC     source_system,
# MAGIC     current_timestamp() AS ingestion_timestamp,
# MAGIC     'BATCH_002' AS batch_id
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC LIMIT 1000;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     batch_id,
# MAGIC     ingestion_timestamp,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo
# MAGIC GROUP BY batch_id, ingestion_timestamp;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 1 — Identify the latest batch# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     batch_id,
# MAGIC     ingestion_timestamp,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo
# MAGIC GROUP BY batch_id, ingestion_timestamp
# MAGIC ORDER BY ingestion_timestamp DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 2 — Create a processing control table# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.processed_batches
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     'BATCH_001' AS batch_id,
# MAGIC     current_timestamp() AS processed_at;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.processed_batches;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 3 — Detect unprocessed batches# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     d.batch_id,
# MAGIC     d.ingestion_timestamp,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo d
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.processed_batches p
# MAGIC     ON d.batch_id = p.batch_id
# MAGIC WHERE p.batch_id IS NULL
# MAGIC GROUP BY
# MAGIC     d.batch_id,
# MAGIC     d.ingestion_timestamp
# MAGIC ORDER BY
# MAGIC     d.ingestion_timestamp;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 4 — Process only the new batch# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.new_transactions_to_process
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT d.*
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo d
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.processed_batches p
# MAGIC     ON d.batch_id = p.batch_id
# MAGIC WHERE p.batch_id IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     batch_id,
# MAGIC     COUNT(*) AS records_to_process
# MAGIC FROM Finflow_Project_catalog.bronze.new_transactions_to_process
# MAGIC GROUP BY batch_id;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Mark BATCH_002 as processed# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO Finflow_Project_catalog.bronze.processed_batches
# MAGIC SELECT
# MAGIC     'BATCH_002' AS batch_id,
# MAGIC     current_timestamp() AS processed_at;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.processed_batches
# MAGIC ORDER BY processed_at;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Idempotency test
# MAGIC
# MAGIC Run the same detection query from Step 3 again:# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     d.batch_id,
# MAGIC     d.ingestion_timestamp,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo d
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.processed_batches p
# MAGIC     ON d.batch_id = p.batch_id
# MAGIC WHERE p.batch_id IS NULL
# MAGIC GROUP BY
# MAGIC     d.batch_id,
# MAGIC     d.ingestion_timestamp
# MAGIC ORDER BY
# MAGIC     d.ingestion_timestamp;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     d.batch_id,
# MAGIC     d.ingestion_timestamp,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo d
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.processed_batches p
# MAGIC     ON d.batch_id = p.batch_id
# MAGIC WHERE p.batch_id IS NULL
# MAGIC GROUP BY
# MAGIC     d.batch_id,
# MAGIC     d.ingestion_timestamp
# MAGIC ORDER BY
# MAGIC     d.ingestion_timestamp;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.new_transactions_to_process
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT d.*
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo d
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.processed_batches p
# MAGIC     ON d.batch_id = p.batch_id
# MAGIC WHERE p.batch_id IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     batch_id,
# MAGIC     COUNT(*) AS records_to_process
# MAGIC FROM Finflow_Project_catalog.bronze.new_transactions_to_process
# MAGIC GROUP BY batch_id;

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO Finflow_Project_catalog.bronze.processed_batches
# MAGIC SELECT
# MAGIC     'BATCH_002' AS batch_id,
# MAGIC     current_timestamp() AS processed_at;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.processed_batches
# MAGIC ORDER BY processed_at;

# COMMAND ----------# MAGIC %md
# MAGIC %md# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.processed_batches
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     batch_id,
# MAGIC     MAX(processed_at) AS processed_at
# MAGIC FROM Finflow_Project_catalog.bronze.processed_batches
# MAGIC GROUP BY batch_id;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.processed_batches
# MAGIC ORDER BY processed_at;

# COMMAND ----------# MAGIC %md
# MAGIC %md# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     d.batch_id,
# MAGIC     COUNT(*) AS records_to_process
# MAGIC FROM Finflow_Project_catalog.bronze.transactions_incremental_demo d
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.processed_batches p
# MAGIC     ON d.batch_id = p.batch_id
# MAGIC WHERE p.batch_id IS NULL
# MAGIC GROUP BY d.batch_id;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC If you get that, we've demonstrated the complete lifecycle:
# MAGIC
# MAGIC New batch arrives
# MAGIC       ↓
# MAGIC Detect unprocessed batch
# MAGIC       ↓
# MAGIC Process only that batch
# MAGIC       ↓
# MAGIC Record processing state
# MAGIC       ↓
# MAGIC Next pipeline run
# MAGIC       ↓
# MAGIC Already processed → SKIP
# MAGIC 🧠 What you should remember
# MAGIC
# MAGIC Incremental Processing
# MAGIC
# MAGIC Processing only newly arrived or changed data instead of reprocessing the entire dataset.
# MAGIC
# MAGIC Watermark / processing state
# MAGIC
# MAGIC A value used to determine what data has already been processed.
# MAGIC
# MAGIC Idempotency
# MAGIC
# MAGIC Re-running the same pipeline should not create duplicate processing/results.
# MAGIC
# MAGIC And one important distinction:
# MAGIC
# MAGIC Incremental Processing ≠ MERGE
# MAGIC
# MAGIC Incremental → Which data should I process?
# MAGIC MERGE → How should I insert/update that data in the target?# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC topic - MERGE / UPSERT.# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create a small target table# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.merge_customer_demo
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     first_name,
# MAGIC     last_name,
# MAGIC     city,
# MAGIC     state,
# MAGIC     kyc_status,
# MAGIC     risk_rating
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC LIMIT 5;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.merge_customer_demo;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 2 — Create incoming data# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.merge_customer_incoming
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC SELECT
# MAGIC     'C0000001' AS customer_id,
# MAGIC     'Pooja' AS first_name,
# MAGIC     'Mehta' AS last_name,
# MAGIC     'MUMBAI' AS city,
# MAGIC     'MAHARASHTRA' AS state,
# MAGIC     'VERIFIED' AS kyc_status,
# MAGIC     'HIGH' AS risk_rating
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'C0000006',
# MAGIC     'Rahul',
# MAGIC     'Sharma',
# MAGIC     'PUNE',
# MAGIC     'MAHARASHTRA',
# MAGIC     'VERIFIED',
# MAGIC     'MEDIUM';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.merge_customer_incoming;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 3 — Perform the MERGE# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO Finflow_Project_catalog.bronze.merge_customer_demo AS target
# MAGIC USING Finflow_Project_catalog.bronze.merge_customer_incoming AS source
# MAGIC ON target.customer_id = source.customer_id
# MAGIC
# MAGIC WHEN MATCHED THEN
# MAGIC     UPDATE SET
# MAGIC         target.first_name = source.first_name,
# MAGIC         target.last_name = source.last_name,
# MAGIC         target.city = source.city,
# MAGIC         target.state = source.state,
# MAGIC         target.kyc_status = source.kyc_status,
# MAGIC         target.risk_rating = source.risk_rating
# MAGIC
# MAGIC WHEN NOT MATCHED THEN
# MAGIC     INSERT (
# MAGIC         customer_id,
# MAGIC         first_name,
# MAGIC         last_name,
# MAGIC         city,
# MAGIC         state,
# MAGIC         kyc_status,
# MAGIC         risk_rating
# MAGIC     )
# MAGIC     VALUES (
# MAGIC         source.customer_id,
# MAGIC         source.first_name,
# MAGIC         source.last_name,
# MAGIC         source.city,
# MAGIC         source.state,
# MAGIC         source.kyc_status,
# MAGIC         source.risk_rating
# MAGIC     );

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.merge_customer_demo
# MAGIC ORDER BY customer_id;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 4 — The important production test: run it again# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO Finflow_Project_catalog.bronze.merge_customer_demo AS target
# MAGIC USING Finflow_Project_catalog.bronze.merge_customer_incoming AS source
# MAGIC ON target.customer_id = source.customer_id
# MAGIC
# MAGIC WHEN MATCHED THEN
# MAGIC     UPDATE SET
# MAGIC         target.first_name = source.first_name,
# MAGIC         target.last_name = source.last_name,
# MAGIC         target.city = source.city,
# MAGIC         target.state = source.state,
# MAGIC         target.kyc_status = source.kyc_status,
# MAGIC         target.risk_rating = source.risk_rating
# MAGIC
# MAGIC WHEN NOT MATCHED THEN
# MAGIC     INSERT (
# MAGIC         customer_id,
# MAGIC         first_name,
# MAGIC         last_name,
# MAGIC         city,
# MAGIC         state,
# MAGIC         kyc_status,
# MAGIC         risk_rating
# MAGIC     )
# MAGIC     VALUES (
# MAGIC         source.customer_id,
# MAGIC         source.first_name,
# MAGIC         source.last_name,
# MAGIC         source.city,
# MAGIC         source.state,
# MAGIC         source.kyc_status,
# MAGIC         source.risk_rating
# MAGIC     );

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.merge_customer_demo
# MAGIC GROUP BY customer_id
# MAGIC ORDER BY customer_id;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 5 — What if the source has duplicate keys?# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.merge_duplicate_source
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC SELECT
# MAGIC     'C0000007' AS customer_id,
# MAGIC     'Rahul' AS first_name,
# MAGIC     'Sharma' AS last_name,
# MAGIC     'PUNE' AS city,
# MAGIC     'MAHARASHTRA' AS state,
# MAGIC     'VERIFIED' AS kyc_status,
# MAGIC     'LOW' AS risk_rating,
# MAGIC     TIMESTAMP('2026-09-18 18:00:00') AS update_timestamp
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'C0000007',
# MAGIC     'Rahul',
# MAGIC     'Sharma',
# MAGIC     'MUMBAI',
# MAGIC     'MAHARASHTRA',
# MAGIC     'VERIFIED',
# MAGIC     'HIGH',
# MAGIC     TIMESTAMP('2026-09-18 18:10:00');

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.merge_duplicate_source
# MAGIC GROUP BY customer_id
# MAGIC HAVING COUNT(*) > 1;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 6 — Keep only the latest record per customer# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.merge_duplicate_source_clean
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     first_name,
# MAGIC     last_name,
# MAGIC     city,
# MAGIC     state,
# MAGIC     kyc_status,
# MAGIC     risk_rating,
# MAGIC     update_timestamp
# MAGIC FROM (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY customer_id
# MAGIC             ORDER BY update_timestamp DESC
# MAGIC         ) AS rn
# MAGIC     FROM Finflow_Project_catalog.bronze.merge_duplicate_source
# MAGIC )
# MAGIC WHERE rn = 1;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.merge_duplicate_source_clean;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 8 — MERGE the deduplicated source# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO Finflow_Project_catalog.bronze.merge_customer_demo AS target
# MAGIC USING Finflow_Project_catalog.bronze.merge_duplicate_source_clean AS source
# MAGIC ON target.customer_id = source.customer_id
# MAGIC
# MAGIC WHEN MATCHED THEN
# MAGIC     UPDATE SET
# MAGIC         target.first_name = source.first_name,
# MAGIC         target.last_name = source.last_name,
# MAGIC         target.city = source.city,
# MAGIC         target.state = source.state,
# MAGIC         target.kyc_status = source.kyc_status,
# MAGIC         target.risk_rating = source.risk_rating
# MAGIC
# MAGIC WHEN NOT MATCHED THEN
# MAGIC     INSERT (
# MAGIC         customer_id,
# MAGIC         first_name,
# MAGIC         last_name,
# MAGIC         city,
# MAGIC         state,
# MAGIC         kyc_status,
# MAGIC         risk_rating
# MAGIC     )
# MAGIC     VALUES (
# MAGIC         source.customer_id,
# MAGIC         source.first_name,
# MAGIC         source.last_name,
# MAGIC         source.city,
# MAGIC         source.state,
# MAGIC         source.kyc_status,
# MAGIC         source.risk_rating
# MAGIC     );

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.merge_customer_demo
# MAGIC WHERE customer_id = 'C0000007';

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Topic 3 — Data Quality Gates.# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 1 — Establish quality rules
# MAGIC For our silver.transactions, let's start with practical rules rather than 20 checks at once.
# MAGIC
# MAGIC We'll validate:
# MAGIC
# MAGIC Rule	What we're checking
# MAGIC transaction_id	Must not be NULL
# MAGIC customer_id	Must not be NULL
# MAGIC account_id	Must not be NULL
# MAGIC status	Must be a valid transaction status
# MAGIC amount	NULL amounts should be flagged
# MAGIC duplicates	transaction_id should be unique
# MAGIC
# MAGIC Critical rules stop the pipeline; warning conditions are recorded separately.
# MAGIC
# MAGIC For example, your existing data has 2,488 NULL transaction amounts. That's a data-quality issue, but whether it should block processing depends on the business rule.# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.transaction_quality_gate
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     current_timestamp() AS check_timestamp,
# MAGIC
# MAGIC     COUNT(*) AS total_records,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_id IS NULL THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS null_transaction_id,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN customer_id IS NULL THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS null_customer_id,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN account_id IS NULL THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS null_account_id,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN status NOT IN ('SUCCESS', 'FAILED', 'PENDING', 'REVERSED')
# MAGIC              OR status IS NULL
# MAGIC         THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS invalid_status,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN amount IS NULL THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS null_amount,
# MAGIC
# MAGIC     COUNT(*) -
# MAGIC     COUNT(DISTINCT transaction_id) AS duplicate_transaction_ids
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.transactions;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_gate;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 3 — Define PASS / FAIL
# MAGIC
# MAGIC For FinFlow, let's use these rules:
# MAGIC
# MAGIC Critical rules → pipeline must fail:
# MAGIC
# MAGIC transaction_id NULL      = 0
# MAGIC customer_id NULL         = 0
# MAGIC account_id NULL           = 0
# MAGIC invalid status            = 0
# MAGIC duplicate transaction_id = 0
# MAGIC
# MAGIC Warning rule:
# MAGIC
# MAGIC NULL amount > 0 → WARNING
# MAGIC
# MAGIC We're deliberately not failing the pipeline because of NULL amounts, since your existing FinFlow data contains 2,488 of them and we've already decided they need business handling rather than blindly deleting them.# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     check_timestamp,
# MAGIC     total_records,
# MAGIC     null_transaction_id,
# MAGIC     null_customer_id,
# MAGIC     null_account_id,
# MAGIC     invalid_status,
# MAGIC     null_amount,
# MAGIC     duplicate_transaction_ids,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN null_transaction_id = 0
# MAGIC          AND null_customer_id = 0
# MAGIC          AND null_account_id = 0
# MAGIC          AND invalid_status = 0
# MAGIC          AND duplicate_transaction_ids = 0
# MAGIC         THEN 'PASS'
# MAGIC         ELSE 'FAIL'
# MAGIC     END AS gate_status,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN null_amount = 0
# MAGIC         THEN 'PASS'
# MAGIC         ELSE 'WARNING'
# MAGIC     END AS amount_quality_status
# MAGIC
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_gate;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 4 — Create a failing test case# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 4A — Recreate the test table# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.transaction_quality_test
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     transaction_id,
# MAGIC     transaction_timestamp,
# MAGIC     customer_id,
# MAGIC     account_id,
# MAGIC     merchant_id,
# MAGIC     transaction_type,
# MAGIC     channel,
# MAGIC     amount,
# MAGIC     currency,
# MAGIC     status,
# MAGIC     source_system
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC LIMIT 1000;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Then add our deliberately bad record# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO Finflow_Project_catalog.bronze.transaction_quality_test
# MAGIC VALUES (
# MAGIC     NULL,
# MAGIC     NULL,
# MAGIC     'C0000001',
# MAGIC     'A0000001',
# MAGIC     NULL,
# MAGIC     'CARD_PURCHASE',
# MAGIC     'MOBILE',
# MAGIC     500.00,
# MAGIC     'INR',
# MAGIC     'INVALID_STATUS',
# MAGIC     'TEST_SYSTEM'
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_records
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_test;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 4B — Run the actual quality gate# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN transaction_id IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS null_transaction_id,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN customer_id IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS null_customer_id,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN account_id IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS null_account_id,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN status NOT IN ('SUCCESS', 'FAILED', 'PENDING', 'REVERSED')
# MAGIC                  OR status IS NULL
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS invalid_status,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN amount IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS null_amount
# MAGIC
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_test;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 4C — Convert the checks into PASS/FAIL# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     CASE
# MAGIC         WHEN SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) = 0
# MAGIC          AND SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) = 0
# MAGIC          AND SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) = 0
# MAGIC          AND SUM(
# MAGIC                 CASE
# MAGIC                     WHEN status NOT IN ('SUCCESS', 'FAILED', 'PENDING', 'REVERSED')
# MAGIC                          OR status IS NULL
# MAGIC                     THEN 1
# MAGIC                     ELSE 0
# MAGIC                 END
# MAGIC              ) = 0
# MAGIC         THEN 'PASS'
# MAGIC         ELSE 'FAIL'
# MAGIC     END AS gate_status
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_test;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 5 — Separate valid and invalid records
# MAGIC
# MAGIC 5A. Create a quarantine table# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.transaction_quarantine
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     CASE
# MAGIC         WHEN transaction_id IS NULL THEN 'NULL_TRANSACTION_ID'
# MAGIC         WHEN customer_id IS NULL THEN 'NULL_CUSTOMER_ID'
# MAGIC         WHEN account_id IS NULL THEN 'NULL_ACCOUNT_ID'
# MAGIC         WHEN status NOT IN ('SUCCESS', 'FAILED', 'PENDING', 'REVERSED')
# MAGIC              OR status IS NULL
# MAGIC             THEN 'INVALID_STATUS'
# MAGIC         ELSE 'UNKNOWN'
# MAGIC     END AS rejection_reason,
# MAGIC     current_timestamp() AS quarantined_at
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_test
# MAGIC WHERE transaction_id IS NULL
# MAGIC    OR customer_id IS NULL
# MAGIC    OR account_id IS NULL
# MAGIC    OR status NOT IN ('SUCCESS', 'FAILED', 'PENDING', 'REVERSED')
# MAGIC    OR status IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quarantine;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Step 5B — Create the valid dataset# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.transaction_quality_passed
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_test
# MAGIC WHERE transaction_id IS NOT NULL
# MAGIC   AND customer_id IS NOT NULL
# MAGIC   AND account_id IS NOT NULL
# MAGIC   AND status IN ('SUCCESS', 'FAILED', 'PENDING', 'REVERSED');

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS passed_records
# MAGIC FROM Finflow_Project_catalog.bronze.transaction_quality_passed;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC We don't necessarily throw away bad data.
# MAGIC
# MAGIC We isolate it, record why it failed, and allow good data to continue when the business rules permit it.
# MAGIC
# MAGIC For your interview:
# MAGIC
# MAGIC "I implemented data quality gates with critical validation rules. Valid records proceed downstream, while failed records are quarantined with a rejection reason and timestamp for investigation."
# MAGIC
# MAGIC That's a very solid engineering concept for FinFlow.
