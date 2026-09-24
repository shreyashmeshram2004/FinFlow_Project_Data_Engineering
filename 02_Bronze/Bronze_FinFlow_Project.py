# MAGIC %md
# MAGIC %md
# MAGIC BRONZE LAYER
# MAGIC Bronze layer 0 and Layer 1 and layer 2# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC LAYER 0
# MAGIC
# MAGIC CREATE CATALOG IF NOT EXISTS Finflow_Project_catalog;
# MAGIC USE CATALOG Finflow_Project_catalog;
# MAGIC
# MAGIC CREATE SCHEMA IF NOT EXISTS bronze;
# MAGIC CREATE SCHEMA IF NOT EXISTS silver;
# MAGIC CREATE SCHEMA IF NOT EXISTS gold;
# MAGIC
# MAGIC CREATE VOLUME IF NOT EXISTS bronze.raw_files;
# MAGIC
# MAGIC SELECT *
# MAGIC FROM read_files(
# MAGIC   '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true
# MAGIC )
# MAGIC LIMIT 10;
# MAGIC
# MAGIC SELECT *
# MAGIC FROM read_files(
# MAGIC   '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true
# MAGIC )
# MAGIC LIMIT 0;
# MAGIC
# MAGIC SELECT COUNT(*) AS customer_count
# MAGIC FROM read_files(
# MAGIC   '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true
# MAGIC );
# MAGIC
# MAGIC SELECT *
# MAGIC FROM read_files(
# MAGIC   '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true
# MAGIC )
# MAGIC WHERE kyc_status IS NULL
# MAGIC LIMIT 20;# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC LAYER 1 -# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG Finflow_Project_catalog;
# MAGIC USE SCHEMA bronze;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_catalog(), current_schema();
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.customers
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     current_timestamp() AS ingestion_timestamp
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.customers
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_rows
# MAGIC FROM Finflow_Project_catalog.bronze.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE Finflow_Project_catalog.bronze.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE DETAIL Finflow_Project_catalog.bronze.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.accounts
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     current_timestamp() AS ingestion_timestamp
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/accounts_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_rows
# MAGIC FROM Finflow_Project_catalog.bronze.accounts;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.merchants
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     current_timestamp() AS ingestion_timestamp
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/merchants_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC );SELECT COUNT(*) AS total_rows
# MAGIC FROM Finflow_Project_catalog.bronze.merchants;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.branches
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     current_timestamp() AS ingestion_timestamp
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/branches_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC );
# MAGIC SELECT COUNT(*) AS total_rows
# MAGIC FROM Finflow_Project_catalog.bronze.branches;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.transactions
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     current_timestamp() AS ingestion_timestamp
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/transactions_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC );
# MAGIC SELECT COUNT(*) AS total_rows
# MAGIC FROM Finflow_Project_catalog.bronze.transactions;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.aml_alerts
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     current_timestamp() AS ingestion_timestamp
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/aml_alerts_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC );
# MAGIC SELECT COUNT(*) AS total_rows
# MAGIC FROM Finflow_Project_catalog.bronze.aml_alerts;

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES IN Finflow_Project_catalog.bronze;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS missing_kyc
# MAGIC FROM Finflow_Project_catalog.bronze.customers
# MAGIC WHERE kyc_status IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS missing_customer_id
# MAGIC FROM Finflow_Project_catalog.bronze.accounts
# MAGIC WHERE customer_id IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC LIMIT 5;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS missing_merchant_id
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC WHERE merchant_id IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.customers
# MAGIC GROUP BY customer_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC LAYER 2
# MAGIC
# MAGIC from now on we are on bronze level 2# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC ingection metadata# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.customer_ingestion_test
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     *,
# MAGIC     'customers_source.csv' AS source_file,
# MAGIC     current_timestamp() AS ingestion_timestamp,
# MAGIC     'BATCH_001' AS batch_id
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     'customers_source.csv' AS source_file;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     *,
# MAGIC     'customers_source.csv' AS source_file,
# MAGIC     current_timestamp() AS ingestion_timestamp,
# MAGIC     'BATCH_001' AS batch_id
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC )
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %sql
# MAGIC select current_timestamp() AS ingestion_timestamp

# COMMAND ----------

# MAGIC %sql
# MAGIC select 'BATCH_001' AS batch_id

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     source_file,
# MAGIC     ingestion_timestamp,
# MAGIC     batch_id
# MAGIC FROM Finflow_Project_catalog.bronze.customer_ingestion_test
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC automatic file metadata# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     _metadata.file_path AS source_file
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC )
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC source file tracing# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     _metadata.file_path AS source_file
# MAGIC FROM read_files(
# MAGIC     '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
# MAGIC     format => 'csv',
# MAGIC     header => true
# MAGIC )
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC basic profiling# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_records
# MAGIC FROM Finflow_Project_catalog.bronze.customers;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_records
# MAGIC FROM Finflow_Project_catalog.bronze.accounts;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_records
# MAGIC FROM Finflow_Project_catalog.bronze.transactions;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_records
# MAGIC FROM Finflow_Project_catalog.bronze.merchants;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_records
# MAGIC FROM Finflow_Project_catalog.bronze.branches;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_records
# MAGIC FROM Finflow_Project_catalog.bronze.aml_alerts;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC null and missing data# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(customer_id) AS customer_id_present,
# MAGIC     COUNT(kyc_status) AS kyc_status_present
# MAGIC FROM Finflow_Project_catalog.bronze.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(account_id) AS account_id_present,
# MAGIC     COUNT(customer_id) AS customer_id_present
# MAGIC FROM Finflow_Project_catalog.bronze.accounts;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(transaction_id) AS transaction_id_present,
# MAGIC     COUNT(amount) AS amount_present
# MAGIC FROM Finflow_Project_catalog.bronze.transactions;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(alert_id) AS alert_id_present,
# MAGIC     COUNT(case_status) AS case_status_present
# MAGIC FROM Finflow_Project_catalog.bronze.aml_alerts;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC dulpicate detection# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.customers
# MAGIC GROUP BY customer_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     account_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.accounts
# MAGIC GROUP BY account_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     transaction_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC GROUP BY transaction_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC
# MAGIC LIMIT 20;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Referential Integrity# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS orphan_transactions
# MAGIC FROM Finflow_Project_catalog.bronze.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.merchants m
# MAGIC     ON t.merchant_id = m.merchant_id
# MAGIC WHERE m.merchant_id IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS orphan_accounts
# MAGIC FROM Finflow_Project_catalog.bronze.accounts a
# MAGIC LEFT JOIN Finflow_Project_catalog.bronze.customers c
# MAGIC     ON a.customer_id = c.customer_id
# MAGIC WHERE c.customer_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Domain Validation# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS negative_amounts
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC WHERE amount < 0;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS zero_amounts
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC WHERE amount = 0;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Currency# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     currency,
# MAGIC     COUNT(*) AS transaction_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC GROUP BY currency
# MAGIC ORDER BY transaction_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Transaction Status# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     status,
# MAGIC     COUNT(*) AS transaction_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC GROUP BY status
# MAGIC ORDER BY transaction_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Merchant categories# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC     merchant_category,
# MAGIC     COUNT(*) AS category_count
# MAGIC FROM Finflow_Project_catalog.bronze.merchants
# MAGIC GROUP BY merchant_category
# MAGIC ORDER BY category_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC AML profiling# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     severity,
# MAGIC     COUNT(*) AS alert_count
# MAGIC FROM Finflow_Project_catalog.bronze.aml_alerts
# MAGIC GROUP BY severity
# MAGIC ORDER BY alert_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create our Bronze Data Quality Summary# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.bronze.data_quality_profile
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC SELECT
# MAGIC     'customers' AS table_name,
# MAGIC     COUNT(*) AS total_records,
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_key_records,
# MAGIC     SUM(CASE WHEN kyc_status IS NULL THEN 1 ELSE 0 END) AS null_business_records
# MAGIC FROM Finflow_Project_catalog.bronze.customers
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'accounts',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.bronze.accounts
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'transactions',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'merchants',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN merchant_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN risk_rating IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.bronze.merchants
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'branches',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     0
# MAGIC FROM Finflow_Project_catalog.bronze.branches
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'aml_alerts',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN alert_id IS NULL THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN case_status IS NULL THEN 1 ELSE 0 END)
# MAGIC FROM Finflow_Project_catalog.bronze.aml_alerts;

# COMMAND ----------# MAGIC %md
# MAGIC %md# COMMAND ----------# MAGIC %md
# MAGIC %md
