# FinFlow Interview Notes

## 1. Why Bronze / Silver / Gold?

- Bronze: preserve what arrived and profile it.
- Silver: make the data trusted and standardized.
- Gold: model the data around business questions.
- Analytics: consume Gold to answer business questions.

## 2. How did you handle duplicates?

I first profiled duplicate business keys and checked whether duplicate records were exact or conflicting. Where a canonical record was required, I used `ROW_NUMBER()` with an appropriate ordering rule and retained the selected record.

## 3. Why did you not drop unmapped merchants?

Dropping the transactions would lose financial activity. I used a `LEFT JOIN`, preserved the transaction, and added an `is_unmapped_merchant` flag so downstream users could quantify the data-quality issue.

## 4. Incremental processing vs MERGE

Incremental processing answers **which data should be processed**. MERGE answers **how inserts and updates should be applied to the target**.

## 5. What is a data-quality gate?

A quality check detects problems. A quality gate determines whether the pipeline is allowed to continue based on defined critical rules.

## 6. How was the pipeline orchestrated?

Databricks Lakeflow Jobs was used to create task dependencies from Level 0 through Analytics. Downstream tasks depended on successful completion of upstream tasks.

## 7. What would you monitor in production?

- job and task status
- execution duration
- retry attempts
- failure history
- record counts
- null counts
- duplicate counts
- data-quality gate results
- unexpected volume changes

## 8. Performance principles

Read less → move less → compute less → write efficiently.

Important Spark/Delta topics include predicate pushdown, column pruning, shuffle reduction, partition sizing, broadcast joins, data skew, AQE, small-file management and Delta optimization.
