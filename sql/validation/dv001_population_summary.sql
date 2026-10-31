-- DV-001: Population summary by entity and currency
-- :amount_column and :table_name are selected
-- by the Python runner from an approved allowlist.

SELECT
    legal_entity,
    currency,
    COUNT(*) AS record_count,
    SUM(CAST(ROUND({amount_column} * 100, 0) AS INTEGER))
        AS total_amount_cents
FROM {table_name}
GROUP BY
    legal_entity,
    currency
ORDER BY
    legal_entity,
    currency;
