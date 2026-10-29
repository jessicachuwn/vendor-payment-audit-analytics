-- AP-003: Potential Duplicate Posted Payments
-- Detection rule:
-- Same entity, vendor, payment date, currency and amount

WITH duplicate_groups AS (
    SELECT
        legal_entity,
        vendor_id,
        payment_date,
        currency,
        payment_amount,
        COUNT(*) AS duplicate_count
    FROM ap_payments
    WHERE payment_status = 'Posted'
    GROUP BY
        legal_entity,
        vendor_id,
        payment_date,
        currency,
        payment_amount
    HAVING COUNT(*) > 1
)

SELECT
    p.payment_id,
    p.legal_entity,
    p.vendor_id,
    p.payment_date,
    p.currency,
    p.payment_amount,
    p.payment_status,
    p.batch_id,
    d.duplicate_count
FROM ap_payments p
INNER JOIN duplicate_groups d
    ON p.legal_entity = d.legal_entity
   AND p.vendor_id = d.vendor_id
   AND p.payment_date = d.payment_date
   AND p.currency = d.currency
   AND p.payment_amount = d.payment_amount
WHERE p.payment_status = 'Posted'
ORDER BY
    p.legal_entity,
    p.vendor_id,
    p.payment_date,
    p.payment_amount,
    p.payment_id;
