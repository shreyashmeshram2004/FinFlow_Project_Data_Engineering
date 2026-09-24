# Databricks notebook source
# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.gold.account_analytics;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE Finflow_Project_catalog.bronze.transactions;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     ingestion_timestamp,
# MAGIC     COUNT(*) AS row_count
# MAGIC FROM Finflow_Project_catalog.bronze.transactions
# MAGIC GROUP BY ingestion_timestamp
# MAGIC ORDER BY ingestion_timestamp;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC 01_Customer_Transaction_Analytics# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC A few things worth noticing for your interview:
# MAGIC
# MAGIC CARD_PURCHASE has the highest transaction volume: 379,783.
# MAGIC ATM_WITHDRAWAL has a much higher average successful transaction amount (~15,216) than card/UPI/bank-transfer transactions (~3,100–3,200).
# MAGIC CASH_DEPOSIT also has a high average (~16,379).
# MAGIC This is exactly the kind of pattern Analytics is supposed to expose.# COMMAND ----------

# MAGIC %sql
# MAGIC -- =========================================================
# MAGIC -- 1. CUSTOMER SEGMENT ANALYSIS
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     customer_segment,
# MAGIC     COUNT(*) AS customer_count,
# MAGIC     SUM(total_accounts) AS total_accounts,
# MAGIC     SUM(total_transactions) AS total_transactions,
# MAGIC     SUM(total_transaction_amount) AS total_transaction_amount,
# MAGIC     AVG(average_transaction_amount) AS avg_transaction_amount
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC GROUP BY customer_segment
# MAGIC ORDER BY total_transaction_amount DESC;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 2. CUSTOMER RISK ANALYSIS
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     risk_rating,
# MAGIC     COUNT(*) AS customer_count,
# MAGIC     SUM(total_transactions) AS total_transactions,
# MAGIC     SUM(total_transaction_amount) AS total_transaction_amount,
# MAGIC     AVG(average_transaction_amount) AS avg_transaction_amount
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC GROUP BY risk_rating
# MAGIC ORDER BY total_transaction_amount DESC;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 3. TRANSACTION STATUS ANALYSIS
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     transaction_status,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(amount) AS total_amount,
# MAGIC     AVG(amount) AS average_amount
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY transaction_status
# MAGIC ORDER BY transaction_count DESC;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 4. TRANSACTION CHANNEL ANALYSIS
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     channel,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC         ELSE 0
# MAGIC     END) AS successful_transaction_amount,
# MAGIC     AVG(CASE
# MAGIC         WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC     END) AS average_successful_amount
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY channel
# MAGIC ORDER BY transaction_count DESC;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 5. TRANSACTION TYPE ANALYSIS
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     transaction_type,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC         ELSE 0
# MAGIC     END) AS successful_amount,
# MAGIC     AVG(CASE
# MAGIC         WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC     END) AS average_successful_amount
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY transaction_type
# MAGIC ORDER BY successful_amount DESC;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Branch + AML + Time Analysis# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC What this tells us
# MAGIC 2025-01 → 2025-12: transaction volume stays fairly stable, roughly 77k–85k transactions/month.
# MAGIC Highest transaction volume: July — 85,096
# MAGIC Lowest: February — 76,795
# MAGIC Successful transaction amount is also relatively stable, mostly around ₹333M–₹374M/month.
# MAGIC Highest successful amount: August — ₹373.55M
# MAGIC Lowest: February — ₹333.09M
# MAGIC Average successful transaction amount stays around ₹4.7k–₹4.9k, so there isn't a dramatic monthly shift.
# MAGIC The - month has 991 transactions. That's our bad/missing timestamp bucket and is exactly the kind of data-quality issue we want to notice in a real project.
# MAGIC Monthly successful transaction amount
# MAGIC
# MAGIC FinFlow 2025 monthly successful transaction value.
# MAGIC
# MAGIC ₹320M
# MAGIC ₹340M
# MAGIC ₹360M
# MAGIC ₹380M
# MAGIC Jan 2025
# MAGIC Mar 2025
# MAGIC May 2025
# MAGIC Aug 2025
# MAGIC Oct 2025
# MAGIC Dec 2025
# MAGIC
# MAGIC The '-' bucket contains 991 transactions with missing/unparseable transaction dates and is excluded from the monthly trend.
# MAGIC
# MAGIC One important thing for our project
# MAGIC
# MAGIC Don't "fix" the - bucket by randomly assigning a month.
# MAGIC
# MAGIC We should treat it as a data-quality finding:
# MAGIC
# MAGIC 991 transactions have missing/unparseable transaction timestamps and therefore cannot be reliably attributed to a calendar month.
# MAGIC
# MAGIC That's a nice interview point because it shows you understand that financial analytics shouldn't silently invent dates.# COMMAND ----------

# MAGIC %sql
# MAGIC -- =========================================================
# MAGIC -- 6. BRANCH PERFORMANCE
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     branch_id,
# MAGIC     branch_name,
# MAGIC     city,
# MAGIC     state,
# MAGIC     total_accounts,
# MAGIC     active_accounts,
# MAGIC     total_transactions,
# MAGIC     successful_transactions,
# MAGIC     successful_transaction_amount,
# MAGIC     average_successful_transaction_amount
# MAGIC FROM Finflow_Project_catalog.gold.branch_performance
# MAGIC ORDER BY successful_transaction_amount DESC
# MAGIC LIMIT 20;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 7. AML ALERT SEVERITY
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     severity,
# MAGIC     COUNT(*) AS alert_count,
# MAGIC     SUM(is_high_priority) AS high_priority_alerts,
# MAGIC     SUM(involves_high_risk_party) AS high_risk_party_alerts
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC GROUP BY severity
# MAGIC ORDER BY
# MAGIC     CASE severity
# MAGIC         WHEN 'CRITICAL' THEN 1
# MAGIC         WHEN 'HIGH' THEN 2
# MAGIC         WHEN 'MEDIUM' THEN 3
# MAGIC         WHEN 'LOW' THEN 4
# MAGIC         ELSE 5
# MAGIC     END;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 8. AML CASE STATUS
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     case_status,
# MAGIC     COUNT(*) AS alert_count
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC GROUP BY case_status
# MAGIC ORDER BY alert_count DESC;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 9. HIGH-RISK CUSTOMERS WITH AML ALERTS
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     customer_name,
# MAGIC     customer_risk_rating,
# MAGIC     COUNT(*) AS alert_count,
# MAGIC     SUM(transaction_amount) AS flagged_transaction_amount
# MAGIC FROM Finflow_Project_catalog.gold.aml_risk
# MAGIC WHERE customer_risk_rating IN ('HIGH', 'CRITICAL')
# MAGIC GROUP BY
# MAGIC     customer_id,
# MAGIC     customer_name,
# MAGIC     customer_risk_rating
# MAGIC ORDER BY alert_count DESC
# MAGIC LIMIT 20;
# MAGIC
# MAGIC
# MAGIC -- =========================================================
# MAGIC -- 10. MONTHLY TRANSACTION TREND
# MAGIC -- =========================================================
# MAGIC
# MAGIC SELECT
# MAGIC     DATE_TRUNC('month', transaction_timestamp) AS transaction_month,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(CASE
# MAGIC         WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC         ELSE 0
# MAGIC     END) AS successful_transaction_amount,
# MAGIC     AVG(CASE
# MAGIC         WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC     END) AS average_successful_amount
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY DATE_TRUNC('month', transaction_timestamp)
# MAGIC ORDER BY transaction_month;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC Business & Risk Analytics# COMMAND ----------

# MAGIC %sql
# MAGIC -- 11. TRANSACTION SUCCESS RATE
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_transactions,
# MAGIC     SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_transactions,
# MAGIC     ROUND(
# MAGIC         100.0 * SUM(CASE WHEN transaction_status = 'SUCCESS' THEN 1 ELSE 0 END)
# MAGIC         / COUNT(*),
# MAGIC         2
# MAGIC     ) AS success_rate_pct
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 12. TOP CUSTOMERS BY TRANSACTION VALUE
# MAGIC SELECT
# MAGIC     customer_id,
# MAGIC     CONCAT_WS(' ', first_name, last_name) AS customer_name,
# MAGIC     customer_segment,
# MAGIC     risk_rating AS customer_risk_rating,
# MAGIC     total_transactions,
# MAGIC     total_transaction_amount,
# MAGIC     average_transaction_amount
# MAGIC FROM Finflow_Project_catalog.gold.customer_360
# MAGIC ORDER BY total_transaction_amount DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 13. MERCHANT CATEGORY ANALYSIS
# MAGIC
# MAGIC SELECT
# MAGIC     merchant_category,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS successful_transaction_amount,
# MAGIC     AVG(
# MAGIC         CASE
# MAGIC             WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC         END
# MAGIC     ) AS average_successful_amount
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC WHERE merchant_category IS NOT NULL
# MAGIC GROUP BY merchant_category
# MAGIC ORDER BY successful_transaction_amount DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 14. FINANCIAL RISK ANALYSIS
# MAGIC
# MAGIC SELECT
# MAGIC     transaction_status,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END)
# MAGIC         AS negative_amount_transactions,
# MAGIC     SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS null_amount_transactions,
# MAGIC     SUM(CASE WHEN is_unmapped_merchant = 1 THEN 1 ELSE 0 END)
# MAGIC         AS unmapped_merchant_transactions
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY transaction_status
# MAGIC ORDER BY transaction_count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 15. UNMAPPED MERCHANT IMPACT
# MAGIC
# MAGIC SELECT
# MAGIC     is_unmapped_merchant,
# MAGIC     COUNT(*) AS transaction_count,
# MAGIC     SUM(amount) AS total_transaction_amount,
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN transaction_status = 'SUCCESS' THEN amount
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS successful_transaction_amount
# MAGIC FROM Finflow_Project_catalog.gold.transaction_analytics
# MAGIC GROUP BY is_unmapped_merchant
# MAGIC ORDER BY is_unmapped_merchant;

# COMMAND ----------# MAGIC %md
# MAGIC %md
# MAGIC 1. Merchant analysis
# MAGIC
# MAGIC Your merchant categories are fairly evenly distributed.
# MAGIC
# MAGIC RESTAURANT: 66,314 transactions, ₹187.86M successful value
# MAGIC HEALTHCARE: 64,596, ₹183.65M
# MAGIC UTILITIES: 63,831, ₹182.30M
# MAGIC E_COMMERCE: 64,106, ₹181.97M
# MAGIC JEWELLERY: 63,847, ₹181.86M
# MAGIC TRAVEL: 63,597, ₹179.59M
# MAGIC EDUCATION: 61,299, ₹174.03M
# MAGIC GROCERY: 60,920, ₹174.02M
# MAGIC FUEL: 59,977, ₹172.35M
# MAGIC ELECTRONICS: 59,043, ₹166.97M
# MAGIC
# MAGIC Interesting observation: the average successful transaction is remarkably similar across merchant categories, roughly ₹3.1k–₹3.2k.
# MAGIC
# MAGIC That's actually useful because it tells us the categories differ more in transaction volume than in average transaction size.
# MAGIC
# MAGIC 2. Financial-risk/data-quality analysis
# MAGIC
# MAGIC This one is more interesting.
# MAGIC
# MAGIC Status	Transactions	Negative amounts	NULL amounts	Unmapped merchants
# MAGIC SUCCESS	909,985	216	2,277	2,255
# MAGIC FAILED	49,993	17	129	130
# MAGIC PENDING	20,039	6	40	64
# MAGIC REVERSED	19,983	6	42	53
# MAGIC 🚨 Important finding
# MAGIC
# MAGIC We have 2,488 NULL transaction amounts in total.
# MAGIC
# MAGIC And 245 negative amounts.
# MAGIC
# MAGIC We should not automatically delete or convert either of these to zero.
# MAGIC
# MAGIC For a financial system:
# MAGIC
# MAGIC NULL amount ≠ ₹0 transaction.
# MAGIC
# MAGIC And negative amounts could potentially represent refunds, reversals, adjustments, etc. We'd need a business rule to determine whether they're legitimate.
# MAGIC
# MAGIC That's a very good interview discussion point.
# MAGIC
# MAGIC 3. Unmapped merchant analysis
# MAGIC
# MAGIC We have:
# MAGIC
# MAGIC 997,498 transactions with mapped merchants
# MAGIC 2,502 transactions with unmapped merchant IDs
# MAGIC
# MAGIC So approximately 0.25% of transactions have an unmapped merchant reference.
# MAGIC
# MAGIC More importantly, those transactions represent:
# MAGIC
# MAGIC ₹11.94M total transaction value
# MAGIC
# MAGIC and
# MAGIC
# MAGIC ₹10.75M successful transaction value.
# MAGIC
# MAGIC That's why we made the correct architectural choice earlier:
# MAGIC
# MAGIC Transaction
# MAGIC      ↓
# MAGIC LEFT JOIN Merchant
# MAGIC      ↓
# MAGIC Merchant found? ── YES → merchant information
# MAGIC      │
# MAGIC      NO
# MAGIC      ↓
# MAGIC is_unmapped_merchant = 1
# MAGIC
# MAGIC We preserve the transaction rather than throwing it away.
# MAGIC
# MAGIC That's exactly the kind of thing I'd want you to explain in an interview.
# MAGIC
# MAGIC
# MAGIC FinFlow pipeline
# MAGIC SOURCE FILES
# MAGIC      ↓
# MAGIC LEVEL 0
# MAGIC      ↓
# MAGIC BRONZE
# MAGIC Raw + ingestion metadata + profiling
# MAGIC      ↓
# MAGIC SILVER
# MAGIC Cleaning + standardization + deduplication
# MAGIC      ↓
# MAGIC GOLD
# MAGIC Business-ready dimensional/analytical datasets
# MAGIC      ↓
# MAGIC ANALYTICS
# MAGIC Business questions + KPIs + risk analysis
# MAGIC      ↓
# MAGIC ENGINEERING
# MAGIC Incremental processing + MERGE + Jobs + monitoring
# MAGIC Analytics questions we can now answer
# MAGIC
# MAGIC Customer
# MAGIC
# MAGIC Which segments generate the most transaction value?
# MAGIC Which customers are most active?
# MAGIC Which customers have high transaction value?
# MAGIC How does customer risk relate to activity?
# MAGIC
# MAGIC Transactions
# MAGIC
# MAGIC Success/failure/pending/reversed distribution
# MAGIC Transaction channels
# MAGIC Transaction types
# MAGIC Monthly trends
# MAGIC Average transaction values
# MAGIC
# MAGIC Branches
# MAGIC
# MAGIC Account volume
# MAGIC Active accounts
# MAGIC Transaction volume
# MAGIC Successful transaction value
# MAGIC
# MAGIC AML
# MAGIC
# MAGIC Alert severity
# MAGIC Case status
# MAGIC High-risk customers with alerts
# MAGIC Flagged transaction values
# MAGIC
# MAGIC Merchant
# MAGIC
# MAGIC Category performance
# MAGIC Transaction volume
# MAGIC Successful transaction value
# MAGIC Average transaction size
# MAGIC
# MAGIC Data quality / financial risk
# MAGIC
# MAGIC NULL amounts
# MAGIC Negative amounts
# MAGIC Unmapped merchants
# MAGIC Missing timestamps# COMMAND ----------# MAGIC %md
# MAGIC %md
