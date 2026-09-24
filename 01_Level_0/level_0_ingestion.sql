CREATE CATALOG IF NOT EXISTS Finflow_Project_catalog;
USE CATALOG Finflow_Project_catalog;

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE VOLUME IF NOT EXISTS bronze.raw_files;

SELECT *
FROM read_files(
  '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
  format => 'csv',
  header => true
)
LIMIT 10;

SELECT *
FROM read_files(
  '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
  format => 'csv',
  header => true
)
LIMIT 0;

SELECT COUNT(*) AS customer_count
FROM read_files(
  '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
  format => 'csv',
  header => true
);

SELECT *
FROM read_files(
  '/Volumes/Finflow_Project_catalog/bronze/raw_files/customers_source.csv',
  format => 'csv',
  header => true
)
WHERE kyc_status IS NULL
LIMIT 20;