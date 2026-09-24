# MAGIC %md
# MAGIC %md
# MAGIC Silver Layer# COMMAND ----------



# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC inspect bronze# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC customers record# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.bronze.customers
# MAGIC LIMIT 20;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Duplicate check# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.bronze.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC GROUP BY customer_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT customer_id) AS unique_customers
# MAGIC FROM Finflow_Project_catalog.bronze.customers;

# COMMAND ----------



# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC create silver schema# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS Finflow_Project_catalog.silver;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC First transformation: select + standardize# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.customers
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC
# MAGIC     TRIM(first_name) AS first_name,
# MAGIC     TRIM(last_name) AS last_name,
# MAGIC
# MAGIC     UPPER(TRIM(gender)) AS gender,
# MAGIC
# MAGIC     CAST(date_of_birth AS DATE) AS date_of_birth,
# MAGIC
# MAGIC     UPPER(TRIM(city)) AS city,
# MAGIC     UPPER(TRIM(state)) AS state,
# MAGIC     UPPER(TRIM(country)) AS country,
# MAGIC
# MAGIC     UPPER(TRIM(kyc_status)) AS kyc_status,
# MAGIC     UPPER(TRIM(risk_rating)) AS risk_rating,
# MAGIC     UPPER(TRIM(customer_segment)) AS customer_segment,
# MAGIC
# MAGIC     ingestion_timestamp
# MAGIC
# MAGIC FROM Finflow_Project_catalog.bronze.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.silver.customers;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC NULL handling# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
# MAGIC     SUM(CASE WHEN first_name IS NULL THEN 1 ELSE 0 END) AS null_first_name,
# MAGIC     SUM(CASE WHEN last_name IS NULL THEN 1 ELSE 0 END) AS null_last_name,
# MAGIC     SUM(CASE WHEN date_of_birth IS NULL THEN 1 ELSE 0 END) AS null_dob,
# MAGIC     SUM(CASE WHEN gender IS NULL THEN 1 ELSE 0 END) AS null_gender,
# MAGIC     SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END) AS null_city,
# MAGIC     SUM(CASE WHEN kyc_status IS NULL THEN 1 ELSE 0 END) AS null_kyc,
# MAGIC     SUM(CASE WHEN risk_rating IS NULL THEN 1 ELSE 0 END) AS null_risk_rating,
# MAGIC     SUM(CASE WHEN customer_segment IS NULL THEN 1 ELSE 0 END) AS null_segment
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.customers;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Duplicate customers# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC GROUP BY customer_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     COUNT(DISTINCT ingestion_timestamp) AS distinct_ingestion_times
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC GROUP BY customer_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY distinct_ingestion_times DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS duplicate_customer_ids,
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN first_name_versions = 1
# MAGIC              AND last_name_versions = 1
# MAGIC              AND gender_versions = 1
# MAGIC              AND dob_versions = 1
# MAGIC              AND city_versions = 1
# MAGIC              AND state_versions = 1
# MAGIC              AND country_versions = 1
# MAGIC              AND kyc_versions = 1
# MAGIC              AND risk_versions = 1
# MAGIC              AND segment_versions = 1
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS exact_duplicate_ids,
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN first_name_versions > 1
# MAGIC               OR last_name_versions > 1
# MAGIC               OR gender_versions > 1
# MAGIC               OR dob_versions > 1
# MAGIC               OR city_versions > 1
# MAGIC               OR state_versions > 1
# MAGIC               OR country_versions > 1
# MAGIC               OR kyc_versions > 1
# MAGIC               OR risk_versions > 1
# MAGIC               OR segment_versions > 1
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS conflicting_duplicate_ids
# MAGIC FROM (
# MAGIC     SELECT
# MAGIC         customer_id,
# MAGIC         COUNT(*) AS record_count,
# MAGIC         COUNT(DISTINCT first_name) AS first_name_versions,
# MAGIC         COUNT(DISTINCT last_name) AS last_name_versions,
# MAGIC         COUNT(DISTINCT gender) AS gender_versions,
# MAGIC         COUNT(DISTINCT date_of_birth) AS dob_versions,
# MAGIC         COUNT(DISTINCT city) AS city_versions,
# MAGIC         COUNT(DISTINCT state) AS state_versions,
# MAGIC         COUNT(DISTINCT country) AS country_versions,
# MAGIC         COUNT(DISTINCT kyc_status) AS kyc_versions,
# MAGIC         COUNT(DISTINCT risk_rating) AS risk_versions,
# MAGIC         COUNT(DISTINCT customer_segment) AS segment_versions
# MAGIC     FROM Finflow_Project_catalog.silver.customers
# MAGIC     GROUP BY customer_id
# MAGIC     HAVING COUNT(*) > 1
# MAGIC ) d;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.customers
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH standardized AS (
# MAGIC     SELECT
# MAGIC         customer_id,
# MAGIC         TRIM(first_name) AS first_name,
# MAGIC         TRIM(last_name) AS last_name,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN UPPER(TRIM(gender)) IN ('M', 'MALE') THEN 'M'
# MAGIC             WHEN UPPER(TRIM(gender)) IN ('F', 'FEMALE') THEN 'F'
# MAGIC             WHEN UPPER(TRIM(gender)) IN ('O', 'OTHER') THEN 'O'
# MAGIC             ELSE UPPER(TRIM(gender))
# MAGIC         END AS gender,
# MAGIC
# MAGIC         CAST(date_of_birth AS DATE) AS date_of_birth,
# MAGIC         UPPER(TRIM(city)) AS city,
# MAGIC         UPPER(TRIM(state)) AS state,
# MAGIC         UPPER(TRIM(country)) AS country,
# MAGIC         UPPER(TRIM(kyc_status)) AS kyc_status,
# MAGIC         UPPER(TRIM(risk_rating)) AS risk_rating,
# MAGIC         UPPER(TRIM(customer_segment)) AS customer_segment,
# MAGIC         ingestion_timestamp
# MAGIC     FROM Finflow_Project_catalog.bronze.customers
# MAGIC ),
# MAGIC
# MAGIC deduplicated AS (
# MAGIC     SELECT *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY customer_id
# MAGIC             ORDER BY
# MAGIC                 CASE WHEN country IS NOT NULL THEN 1 ELSE 0 END DESC,
# MAGIC                 CASE WHEN state IS NOT NULL THEN 1 ELSE 0 END DESC,
# MAGIC                 CASE WHEN city IS NOT NULL THEN 1 ELSE 0 END DESC,
# MAGIC                 CASE WHEN kyc_status IS NOT NULL THEN 1 ELSE 0 END DESC,
# MAGIC                 CASE WHEN risk_rating IS NOT NULL THEN 1 ELSE 0 END DESC,
# MAGIC                 CASE WHEN customer_segment IS NOT NULL THEN 1 ELSE 0 END DESC
# MAGIC         ) AS rn
# MAGIC     FROM standardized
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     first_name,
# MAGIC     last_name,
# MAGIC     gender,
# MAGIC     date_of_birth,
# MAGIC     city,
# MAGIC     state,
# MAGIC     country,
# MAGIC     kyc_status,
# MAGIC     risk_rating,
# MAGIC     customer_segment,
# MAGIC     ingestion_timestamp
# MAGIC FROM deduplicated
# MAGIC WHERE rn = 1;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT customer_id) AS unique_customers,
# MAGIC     COUNT(*) - COUNT(DISTINCT customer_id) AS duplicate_records,
# MAGIC     COUNT(DISTINCT gender) AS gender_categories
# MAGIC FROM Finflow_Project_catalog.silver.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT customer_id) AS unique_customer_ids
# MAGIC FROM Finflow_Project_catalog.silver.customers;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Business-value validation# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC KYC values# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     kyc_status,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC GROUP BY kyc_status
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Risk ratings# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     risk_rating,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC GROUP BY risk_rating
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Customer segments# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     customer_segment,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC GROUP BY customer_segment
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Gender# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     gender,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC GROUP BY gender
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Date validation# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     MIN(date_of_birth) AS earliest_dob,
# MAGIC     MAX(date_of_birth) AS latest_dob,
# MAGIC     COUNT(*) AS total_records,
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN date_of_birth > CURRENT_DATE() THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS future_dob_records
# MAGIC FROM Finflow_Project_catalog.silver.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC LIMIT 10;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC accounts record# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.bronze.accounts;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create silver.accounts# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.accounts
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     account_id,
# MAGIC     customer_id,
# MAGIC     TRIM(account_type) AS account_type,
# MAGIC     branch_id,
# MAGIC     UPPER(TRIM(currency)) AS currency,
# MAGIC     CAST(opening_date AS DATE) AS opening_date,
# MAGIC     UPPER(TRIM(status)) AS status,
# MAGIC     CAST(credit_limit AS DECIMAL(18,2)) AS credit_limit,
# MAGIC     ingestion_timestamp
# MAGIC FROM Finflow_Project_catalog.bronze.accounts;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC profile the silver table# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT account_id) AS unique_accounts,
# MAGIC
# MAGIC     SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS null_account_id,
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
# MAGIC     SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END) AS null_branch_id,
# MAGIC     SUM(CASE WHEN account_type IS NULL THEN 1 ELSE 0 END) AS null_account_type,
# MAGIC     SUM(CASE WHEN currency IS NULL THEN 1 ELSE 0 END) AS null_currency,
# MAGIC     SUM(CASE WHEN opening_date IS NULL THEN 1 ELSE 0 END) AS null_opening_date,
# MAGIC     SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) AS null_status,
# MAGIC     SUM(CASE WHEN credit_limit IS NULL THEN 1 ELSE 0 END) AS null_credit_limit
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.accounts;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT account_type, COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC GROUP BY account_type
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT status, COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC GROUP BY status
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT currency, COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC GROUP BY currency
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Check duplicate account IDs# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     account_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC GROUP BY account_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Check impossible dates / credit limits# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS invalid_records
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC WHERE opening_date > CURRENT_DATE()
# MAGIC    OR credit_limit < 0;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC relationships# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     a.account_id,
# MAGIC     a.customer_id
# MAGIC FROM Finflow_Project_catalog.silver.accounts a
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON a.customer_id = c.customer_id
# MAGIC WHERE a.customer_id IS NOT NULL
# MAGIC   AND c.customer_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC transactions records# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.bronze.transactions;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create silver.transactions# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.transactions
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     transaction_id,
# MAGIC
# MAGIC     COALESCE(
# MAGIC         try_to_timestamp(transaction_timestamp, 'yyyy-MM-dd HH:mm:ss'),
# MAGIC         try_to_timestamp(transaction_timestamp, 'yyyy/MM/dd HH:mm:ss')
# MAGIC     ) AS transaction_timestamp,
# MAGIC
# MAGIC     customer_id,
# MAGIC     account_id,
# MAGIC     merchant_id,
# MAGIC
# MAGIC     UPPER(TRIM(transaction_type)) AS transaction_type,
# MAGIC     UPPER(TRIM(channel)) AS channel,
# MAGIC
# MAGIC     CAST(amount AS DECIMAL(18,2)) AS amount,
# MAGIC
# MAGIC     UPPER(TRIM(currency)) AS currency,
# MAGIC     UPPER(TRIM(status)) AS status,
# MAGIC     UPPER(TRIM(source_system)) AS source_system,
# MAGIC
# MAGIC     ingestion_timestamp
# MAGIC
# MAGIC FROM Finflow_Project_catalog.bronze.transactions;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     transaction_id,
# MAGIC     transaction_timestamp
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC LIMIT 20;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Profile transactions# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT transaction_id) AS unique_transactions,
# MAGIC
# MAGIC     SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) AS null_transaction_id,
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
# MAGIC     SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS null_account_id,
# MAGIC     SUM(CASE WHEN merchant_id IS NULL THEN 1 ELSE 0 END) AS null_merchant_id,
# MAGIC     SUM(CASE WHEN transaction_timestamp IS NULL THEN 1 ELSE 0 END) AS null_timestamp,
# MAGIC     SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) AS null_amount,
# MAGIC     SUM(CASE WHEN currency IS NULL THEN 1 ELSE 0 END) AS null_currency,
# MAGIC     SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) AS null_status
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.transactions;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     transaction_type,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC GROUP BY transaction_type
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     channel,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC GROUP BY channel
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     status,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC GROUP BY status
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Financial validation# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     MIN(amount) AS minimum_amount,
# MAGIC     MAX(amount) AS maximum_amount,
# MAGIC     AVG(amount) AS average_amount,
# MAGIC     SUM(CASE WHEN amount <= 0 THEN 1 ELSE 0 END) AS non_positive_amounts
# MAGIC FROM Finflow_Project_catalog.silver.transactions;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Duplicate transactions# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     transaction_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC GROUP BY transaction_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Referential integrity# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     t.transaction_id,
# MAGIC     t.account_id
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.accounts a
# MAGIC     ON t.account_id = a.account_id
# MAGIC WHERE t.account_id IS NOT NULL
# MAGIC   AND a.account_id IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     t.transaction_id,
# MAGIC     t.account_id
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.accounts a
# MAGIC     ON t.account_id = a.account_id
# MAGIC WHERE t.account_id IS NOT NULL
# MAGIC   AND a.account_id IS NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     t.transaction_id,
# MAGIC     t.customer_id
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON t.customer_id = c.customer_id
# MAGIC WHERE t.customer_id IS NOT NULL
# MAGIC   AND c.customer_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC merchants record# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.bronze.merchants;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Standardize merchants# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.merchants
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     merchant_id,
# MAGIC     TRIM(merchant_name) AS merchant_name,
# MAGIC     UPPER(TRIM(merchant_category)) AS merchant_category,
# MAGIC     UPPER(TRIM(city)) AS city,
# MAGIC     UPPER(TRIM(state)) AS state,
# MAGIC     UPPER(TRIM(country)) AS country,
# MAGIC     UPPER(TRIM(risk_rating)) AS risk_rating,
# MAGIC     ingestion_timestamp
# MAGIC FROM Finflow_Project_catalog.bronze.merchants;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Profile# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT merchant_id) AS unique_merchants,
# MAGIC
# MAGIC     SUM(CASE WHEN merchant_id IS NULL THEN 1 ELSE 0 END) AS null_merchant_id,
# MAGIC     SUM(CASE WHEN merchant_name IS NULL THEN 1 ELSE 0 END) AS null_merchant_name,
# MAGIC     SUM(CASE WHEN merchant_category IS NULL THEN 1 ELSE 0 END) AS null_category,
# MAGIC     SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END) AS null_city,
# MAGIC     SUM(CASE WHEN risk_rating IS NULL THEN 1 ELSE 0 END) AS null_risk_rating
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.merchants;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     merchant_category,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.merchants
# MAGIC GROUP BY merchant_category
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     merchant_category,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.merchants
# MAGIC GROUP BY merchant_category
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Duplicate check# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     merchant_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.merchants
# MAGIC GROUP BY merchant_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC transaction → merchant check# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     t.transaction_id,
# MAGIC     t.merchant_id
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.merchants m
# MAGIC     ON t.merchant_id = m.merchant_id
# MAGIC WHERE t.merchant_id IS NOT NULL
# MAGIC   AND m.merchant_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Branches record# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.bronze.branches;
# MAGIC

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create the Silver table# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.branches
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     branch_id,
# MAGIC     TRIM(branch_name) AS branch_name,
# MAGIC     UPPER(TRIM(city)) AS city,
# MAGIC     UPPER(TRIM(state)) AS state,
# MAGIC     UPPER(TRIM(branch_type)) AS branch_type,
# MAGIC     ingestion_timestamp
# MAGIC FROM Finflow_Project_catalog.bronze.branches;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Profile it# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT branch_id) AS unique_branches,
# MAGIC
# MAGIC     SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END) AS null_branch_id,
# MAGIC     SUM(CASE WHEN branch_name IS NULL THEN 1 ELSE 0 END) AS null_branch_name,
# MAGIC     SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END) AS null_city,
# MAGIC     SUM(CASE WHEN state IS NULL THEN 1 ELSE 0 END) AS null_state,
# MAGIC     SUM(CASE WHEN branch_type IS NULL THEN 1 ELSE 0 END) AS null_branch_type
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.branches;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Check branch types# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     branch_type,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.branches
# MAGIC GROUP BY branch_type
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Check duplicates# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     branch_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.branches
# MAGIC GROUP BY branch_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Check the account → branch relationship# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     a.account_id,
# MAGIC     a.branch_id
# MAGIC FROM Finflow_Project_catalog.silver.accounts a
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.branches b
# MAGIC     ON a.branch_id = b.branch_id
# MAGIC WHERE a.branch_id IS NOT NULL
# MAGIC   AND b.branch_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC aml_alerts# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create Silver Branches# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.branches
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     branch_id,
# MAGIC     TRIM(branch_name) AS branch_name,
# MAGIC     UPPER(TRIM(city)) AS city,
# MAGIC     UPPER(TRIM(state)) AS state,
# MAGIC     UPPER(TRIM(branch_type)) AS branch_type,
# MAGIC     ingestion_timestamp
# MAGIC FROM Finflow_Project_catalog.bronze.branches;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC profile it# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT branch_id) AS unique_branches,
# MAGIC     SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END) AS null_branch_id,
# MAGIC     SUM(CASE WHEN branch_name IS NULL THEN 1 ELSE 0 END) AS null_branch_name,
# MAGIC     SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END) AS null_city,
# MAGIC     SUM(CASE WHEN state IS NULL THEN 1 ELSE 0 END) AS null_state,
# MAGIC     SUM(CASE WHEN branch_type IS NULL THEN 1 ELSE 0 END) AS null_branch_type
# MAGIC FROM Finflow_Project_catalog.silver.branches;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC check branch type# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     branch_type,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.branches
# MAGIC GROUP BY branch_type
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC duplicate branches# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     branch_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.branches
# MAGIC GROUP BY branch_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC account branch relationship# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     a.account_id,
# MAGIC     a.branch_id
# MAGIC FROM Finflow_Project_catalog.silver.accounts a
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.branches b
# MAGIC     ON a.branch_id = b.branch_id
# MAGIC WHERE a.branch_id IS NOT NULL
# MAGIC   AND b.branch_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC aml alreat record# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.bronze.aml_alerts;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Create silver.aml_alerts# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.aml_alerts
# MAGIC USING DELTA
# MAGIC AS
# MAGIC SELECT
# MAGIC     alert_id,
# MAGIC     transaction_id,
# MAGIC     customer_id,
# MAGIC     CAST(alert_timestamp AS TIMESTAMP) AS alert_timestamp,
# MAGIC     UPPER(TRIM(alert_type)) AS alert_type,
# MAGIC     UPPER(TRIM(severity)) AS severity,
# MAGIC     UPPER(TRIM(case_status)) AS case_status,
# MAGIC     TRIM(investigator) AS investigator,
# MAGIC     ingestion_timestamp
# MAGIC FROM Finflow_Project_catalog.bronze.aml_alerts;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC profile# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT alert_id) AS unique_alerts,
# MAGIC
# MAGIC     SUM(CASE WHEN alert_id IS NULL THEN 1 ELSE 0 END) AS null_alert_id,
# MAGIC     SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) AS null_transaction_id,
# MAGIC     SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
# MAGIC     SUM(CASE WHEN alert_timestamp IS NULL THEN 1 ELSE 0 END) AS null_alert_timestamp,
# MAGIC     SUM(CASE WHEN alert_type IS NULL THEN 1 ELSE 0 END) AS null_alert_type,
# MAGIC     SUM(CASE WHEN severity IS NULL THEN 1 ELSE 0 END) AS null_severity,
# MAGIC     SUM(CASE WHEN case_status IS NULL THEN 1 ELSE 0 END) AS null_case_status,
# MAGIC     SUM(CASE WHEN investigator IS NULL THEN 1 ELSE 0 END) AS null_investigator
# MAGIC
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC profile aml categories# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC alert type# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     alert_type,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC GROUP BY alert_type
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Severity# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     severity,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC GROUP BY severity
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Case status# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     case_status,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC GROUP BY case_status
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC duplicate alert# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     alert_id,
# MAGIC     COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC GROUP BY alert_id
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY record_count DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC future alert timestamp# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS future_alerts
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC WHERE alert_timestamp > CURRENT_TIMESTAMP();

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Relationship check# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Alert → Transaction# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     a.alert_id,
# MAGIC     a.transaction_id
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts a
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.transactions t
# MAGIC     ON a.transaction_id = t.transaction_id
# MAGIC WHERE a.transaction_id IS NOT NULL
# MAGIC   AND t.transaction_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Alert → Customer# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     a.alert_id,
# MAGIC     a.customer_id
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts a
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON a.customer_id = c.customer_id
# MAGIC WHERE a.customer_id IS NOT NULL
# MAGIC   AND c.customer_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Silver sanity check# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'customers' AS table_name, COUNT(*) AS record_count
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'accounts', COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'transactions', COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'merchants', COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.merchants
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'branches', COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.branches
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'aml_alerts', COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts;

# COMMAND ----------# MAGIC %md
# MAGIC %md# COMMAND ----------# MAGIC %md
# MAGIC %md# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC solving problem such as duplication we have solved problem in account record problem earlier# COMMAND ----------

# MAGIC %sql
# MAGIC -- ============================================================
# MAGIC -- SILVER READINESS CHECK
# MAGIC -- ============================================================
# MAGIC
# MAGIC WITH
# MAGIC customer_check AS (
# MAGIC     SELECT
# MAGIC         'customers' AS table_name,
# MAGIC         COUNT(*) AS total_rows,
# MAGIC         COUNT(DISTINCT customer_id) AS unique_keys,
# MAGIC         SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_keys
# MAGIC     FROM Finflow_Project_catalog.silver.customers
# MAGIC ),
# MAGIC
# MAGIC account_check AS (
# MAGIC     SELECT
# MAGIC         'accounts',
# MAGIC         COUNT(*),
# MAGIC         COUNT(DISTINCT account_id),
# MAGIC         SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END)
# MAGIC     FROM Finflow_Project_catalog.silver.accounts
# MAGIC ),
# MAGIC
# MAGIC transaction_check AS (
# MAGIC     SELECT
# MAGIC         'transactions',
# MAGIC         COUNT(*),
# MAGIC         COUNT(DISTINCT transaction_id),
# MAGIC         SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END)
# MAGIC     FROM Finflow_Project_catalog.silver.transactions
# MAGIC ),
# MAGIC
# MAGIC merchant_check AS (
# MAGIC     SELECT
# MAGIC         'merchants',
# MAGIC         COUNT(*),
# MAGIC         COUNT(DISTINCT merchant_id),
# MAGIC         SUM(CASE WHEN merchant_id IS NULL THEN 1 ELSE 0 END)
# MAGIC     FROM Finflow_Project_catalog.silver.merchants
# MAGIC ),
# MAGIC
# MAGIC branch_check AS (
# MAGIC     SELECT
# MAGIC         'branches',
# MAGIC         COUNT(*),
# MAGIC         COUNT(DISTINCT branch_id),
# MAGIC         SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END)
# MAGIC     FROM Finflow_Project_catalog.silver.branches
# MAGIC ),
# MAGIC
# MAGIC aml_check AS (
# MAGIC     SELECT
# MAGIC         'aml_alerts',
# MAGIC         COUNT(*),
# MAGIC         COUNT(DISTINCT alert_id),
# MAGIC         SUM(CASE WHEN alert_id IS NULL THEN 1 ELSE 0 END)
# MAGIC     FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC )
# MAGIC
# MAGIC SELECT * FROM customer_check
# MAGIC UNION ALL
# MAGIC SELECT * FROM account_check
# MAGIC UNION ALL
# MAGIC SELECT * FROM transaction_check
# MAGIC UNION ALL
# MAGIC SELECT * FROM merchant_check
# MAGIC UNION ALL
# MAGIC SELECT * FROM branch_check
# MAGIC UNION ALL
# MAGIC SELECT * FROM aml_check
# MAGIC ORDER BY table_name;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ============================================================
# MAGIC -- SILVER REFERENTIAL INTEGRITY CHECK
# MAGIC -- ============================================================
# MAGIC
# MAGIC SELECT 'accounts → customers' AS relationship,
# MAGIC        COUNT(*) AS orphan_records
# MAGIC FROM Finflow_Project_catalog.silver.accounts a
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON a.customer_id = c.customer_id
# MAGIC WHERE a.customer_id IS NOT NULL
# MAGIC   AND c.customer_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'accounts → branches',
# MAGIC        COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.accounts a
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.branches b
# MAGIC     ON a.branch_id = b.branch_id
# MAGIC WHERE a.branch_id IS NOT NULL
# MAGIC   AND b.branch_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'transactions → customers',
# MAGIC        COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON t.customer_id = c.customer_id
# MAGIC WHERE t.customer_id IS NOT NULL
# MAGIC   AND c.customer_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'transactions → accounts',
# MAGIC        COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.accounts a
# MAGIC     ON t.account_id = a.account_id
# MAGIC WHERE t.account_id IS NOT NULL
# MAGIC   AND a.account_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'transactions → merchants',
# MAGIC        COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.transactions t
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.merchants m
# MAGIC     ON t.merchant_id = m.merchant_id
# MAGIC WHERE t.merchant_id IS NOT NULL
# MAGIC   AND m.merchant_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'AML → transactions',
# MAGIC        COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts al
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.transactions t
# MAGIC     ON al.transaction_id = t.transaction_id
# MAGIC WHERE al.transaction_id IS NOT NULL
# MAGIC   AND t.transaction_id IS NULL
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 'AML → customers',
# MAGIC        COUNT(*)
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts al
# MAGIC LEFT JOIN Finflow_Project_catalog.silver.customers c
# MAGIC     ON al.customer_id = c.customer_id
# MAGIC WHERE al.customer_id IS NOT NULL
# MAGIC   AND c.customer_id IS NULL;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Bronze
# MAGIC    ↓
# MAGIC Silver transformation
# MAGIC    ↓
# MAGIC QUALITY GATE
# MAGIC    ↓
# MAGIC ❌ Accounts duplicates
# MAGIC ❌ Transaction duplicates
# MAGIC ❌ Merchant duplicates
# MAGIC ❌ Branch duplicates
# MAGIC ❌ AML duplicates
# MAGIC ❌ 2,513 broken merchant references
# MAGIC    ↓
# MAGIC FIX
# MAGIC    ↓
# MAGIC QUALITY GATE again
# MAGIC    ↓
# MAGIC Silver ✅
# MAGIC    ↓
# MAGIC Gold# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Duplicate-key handling uses a business key, ROW_NUMBER(), and retention of the canonical record.
# MAGIC
# MAGIC PARTITION BY business_key
# MAGIC         ↓
# MAGIC ROW_NUMBER()
# MAGIC         ↓
# MAGIC keep rn = 1# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     'accounts' AS table_name,
# MAGIC     COUNT(*) AS duplicate_keys,
# MAGIC     SUM(CASE WHEN distinct_versions = 1 THEN 1 ELSE 0 END) AS exact_duplicates,
# MAGIC     SUM(CASE WHEN distinct_versions > 1 THEN 1 ELSE 0 END) AS conflicting_duplicates
# MAGIC FROM (
# MAGIC     SELECT
# MAGIC         account_id,
# MAGIC         COUNT(DISTINCT CONCAT_WS('|',
# MAGIC             customer_id,
# MAGIC             account_type,
# MAGIC             branch_id,
# MAGIC             currency,
# MAGIC             CAST(opening_date AS STRING),
# MAGIC             status,
# MAGIC             CAST(credit_limit AS STRING)
# MAGIC         )) AS distinct_versions
# MAGIC     FROM Finflow_Project_catalog.silver.accounts
# MAGIC     GROUP BY account_id
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'transactions',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN distinct_versions = 1 THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN distinct_versions > 1 THEN 1 ELSE 0 END)
# MAGIC FROM (
# MAGIC     SELECT
# MAGIC         transaction_id,
# MAGIC         COUNT(DISTINCT CONCAT_WS('|',
# MAGIC             customer_id,
# MAGIC             account_id,
# MAGIC             merchant_id,
# MAGIC             CAST(transaction_timestamp AS STRING),
# MAGIC             transaction_type,
# MAGIC             channel,
# MAGIC             CAST(amount AS STRING),
# MAGIC             currency,
# MAGIC             status,
# MAGIC             source_system
# MAGIC         )) AS distinct_versions
# MAGIC     FROM Finflow_Project_catalog.silver.transactions
# MAGIC     GROUP BY transaction_id
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'merchants',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN distinct_versions = 1 THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN distinct_versions > 1 THEN 1 ELSE 0 END)
# MAGIC FROM (
# MAGIC     SELECT
# MAGIC         merchant_id,
# MAGIC         COUNT(DISTINCT CONCAT_WS('|',
# MAGIC             merchant_name,
# MAGIC             merchant_category,
# MAGIC             city,
# MAGIC             state,
# MAGIC             country,
# MAGIC             risk_rating
# MAGIC         )) AS distinct_versions
# MAGIC     FROM Finflow_Project_catalog.silver.merchants
# MAGIC     GROUP BY merchant_id
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'branches',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN distinct_versions = 1 THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN distinct_versions > 1 THEN 1 ELSE 0 END)
# MAGIC FROM (
# MAGIC     SELECT
# MAGIC         branch_id,
# MAGIC         COUNT(DISTINCT CONCAT_WS('|',
# MAGIC             branch_name,
# MAGIC             city,
# MAGIC             state,
# MAGIC             branch_type
# MAGIC         )) AS distinct_versions
# MAGIC     FROM Finflow_Project_catalog.silver.branches
# MAGIC     GROUP BY branch_id
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'aml_alerts',
# MAGIC     COUNT(*),
# MAGIC     SUM(CASE WHEN distinct_versions = 1 THEN 1 ELSE 0 END),
# MAGIC     SUM(CASE WHEN distinct_versions > 1 THEN 1 ELSE 0 END)
# MAGIC FROM (
# MAGIC     SELECT
# MAGIC         alert_id,
# MAGIC         COUNT(DISTINCT CONCAT_WS('|',
# MAGIC             transaction_id,
# MAGIC             customer_id,
# MAGIC             CAST(alert_timestamp AS STRING),
# MAGIC             alert_type,
# MAGIC             severity,
# MAGIC             case_status,
# MAGIC             investigator
# MAGIC         )) AS distinct_versions
# MAGIC     FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC     GROUP BY alert_id
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC ORDER BY table_name;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ============================================================
# MAGIC -- SILVER DEDUPLICATION
# MAGIC -- Keep the most complete record for each business key.
# MAGIC -- Exact duplicates are automatically reduced to one record.
# MAGIC -- ============================================================
# MAGIC
# MAGIC
# MAGIC -- ============================================================
# MAGIC -- ACCOUNTS
# MAGIC -- ============================================================
# MAGIC
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.accounts
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH ranked AS (
# MAGIC     SELECT *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY account_id
# MAGIC             ORDER BY
# MAGIC                 (
# MAGIC                     CASE WHEN customer_id IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN account_type IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN branch_id IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN currency IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN opening_date IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN status IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN credit_limit IS NOT NULL THEN 1 ELSE 0 END
# MAGIC                 ) DESC,
# MAGIC                 ingestion_timestamp DESC
# MAGIC         ) AS rn
# MAGIC     FROM Finflow_Project_catalog.silver.accounts
# MAGIC )
# MAGIC SELECT
# MAGIC     account_id,
# MAGIC     customer_id,
# MAGIC     account_type,
# MAGIC     branch_id,
# MAGIC     currency,
# MAGIC     opening_date,
# MAGIC     status,
# MAGIC     credit_limit,
# MAGIC     ingestion_timestamp
# MAGIC FROM ranked
# MAGIC WHERE rn = 1;
# MAGIC
# MAGIC
# MAGIC -- ============================================================
# MAGIC -- TRANSACTIONS
# MAGIC -- ============================================================
# MAGIC
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.transactions
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH ranked AS (
# MAGIC     SELECT *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY transaction_id
# MAGIC             ORDER BY
# MAGIC                 (
# MAGIC                     CASE WHEN transaction_timestamp IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN customer_id IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN account_id IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN merchant_id IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN transaction_type IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN channel IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN amount IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN currency IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN status IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN source_system IS NOT NULL THEN 1 ELSE 0 END
# MAGIC                 ) DESC,
# MAGIC                 ingestion_timestamp DESC
# MAGIC         ) AS rn
# MAGIC     FROM Finflow_Project_catalog.silver.transactions
# MAGIC )
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
# MAGIC     ingestion_timestamp
# MAGIC FROM ranked
# MAGIC WHERE rn = 1;
# MAGIC
# MAGIC
# MAGIC -- ============================================================
# MAGIC -- MERCHANTS
# MAGIC -- ============================================================
# MAGIC
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.merchants
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH ranked AS (
# MAGIC     SELECT *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY merchant_id
# MAGIC             ORDER BY
# MAGIC                 (
# MAGIC                     CASE WHEN merchant_name IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN merchant_category IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN city IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN state IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN country IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN risk_rating IS NOT NULL THEN 1 ELSE 0 END
# MAGIC                 ) DESC,
# MAGIC                 ingestion_timestamp DESC
# MAGIC         ) AS rn
# MAGIC     FROM Finflow_Project_catalog.silver.merchants
# MAGIC )
# MAGIC SELECT
# MAGIC     merchant_id,
# MAGIC     merchant_name,
# MAGIC     merchant_category,
# MAGIC     city,
# MAGIC     state,
# MAGIC     country,
# MAGIC     risk_rating,
# MAGIC     ingestion_timestamp
# MAGIC FROM ranked
# MAGIC WHERE rn = 1;
# MAGIC
# MAGIC
# MAGIC -- ============================================================
# MAGIC -- BRANCHES
# MAGIC -- ============================================================
# MAGIC
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.branches
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH ranked AS (
# MAGIC     SELECT *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY branch_id
# MAGIC             ORDER BY
# MAGIC                 (
# MAGIC                     CASE WHEN branch_name IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN city IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN state IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN branch_type IS NOT NULL THEN 1 ELSE 0 END
# MAGIC                 ) DESC,
# MAGIC                 ingestion_timestamp DESC
# MAGIC         ) AS rn
# MAGIC     FROM Finflow_Project_catalog.silver.branches
# MAGIC )
# MAGIC SELECT
# MAGIC     branch_id,
# MAGIC     branch_name,
# MAGIC     city,
# MAGIC     state,
# MAGIC     branch_type,
# MAGIC     ingestion_timestamp
# MAGIC FROM ranked
# MAGIC WHERE rn = 1;
# MAGIC
# MAGIC
# MAGIC -- ============================================================
# MAGIC -- AML ALERTS
# MAGIC -- ============================================================
# MAGIC
# MAGIC CREATE OR REPLACE TABLE Finflow_Project_catalog.silver.aml_alerts
# MAGIC USING DELTA
# MAGIC AS
# MAGIC WITH ranked AS (
# MAGIC     SELECT *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY alert_id
# MAGIC             ORDER BY
# MAGIC                 (
# MAGIC                     CASE WHEN transaction_id IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN customer_id IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN alert_timestamp IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN alert_type IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN severity IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN case_status IS NOT NULL THEN 1 ELSE 0 END +
# MAGIC                     CASE WHEN investigator IS NOT NULL THEN 1 ELSE 0 END
# MAGIC                 ) DESC,
# MAGIC                 ingestion_timestamp DESC
# MAGIC         ) AS rn
# MAGIC     FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC )
# MAGIC SELECT
# MAGIC     alert_id,
# MAGIC     transaction_id,
# MAGIC     customer_id,
# MAGIC     alert_timestamp,
# MAGIC     alert_type,
# MAGIC     severity,
# MAGIC     case_status,
# MAGIC     investigator,
# MAGIC     ingestion_timestamp
# MAGIC FROM ranked
# MAGIC WHERE rn = 1;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     'customers' AS table_name,
# MAGIC     COUNT(*) AS total_rows,
# MAGIC     COUNT(DISTINCT customer_id) AS unique_keys
# MAGIC FROM Finflow_Project_catalog.silver.customers
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'accounts',
# MAGIC     COUNT(*),
# MAGIC     COUNT(DISTINCT account_id)
# MAGIC FROM Finflow_Project_catalog.silver.accounts
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'transactions',
# MAGIC     COUNT(*),
# MAGIC     COUNT(DISTINCT transaction_id)
# MAGIC FROM Finflow_Project_catalog.silver.transactions
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'merchants',
# MAGIC     COUNT(*),
# MAGIC     COUNT(DISTINCT merchant_id)
# MAGIC FROM Finflow_Project_catalog.silver.merchants
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'branches',
# MAGIC     COUNT(*),
# MAGIC     COUNT(DISTINCT branch_id)
# MAGIC FROM Finflow_Project_catalog.silver.branches
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC     'aml_alerts',
# MAGIC     COUNT(*),
# MAGIC     COUNT(DISTINCT alert_id)
# MAGIC FROM Finflow_Project_catalog.silver.aml_alerts
# MAGIC
# MAGIC ORDER BY table_name;
