-- AP-003E: Duplicate Payment Invoice Investigation

WITH duplicate_payments AS (
    SELECT
        payment_id,
        legal_entity,
        vendor_id,
        payment_date,
        currency,
        payment_amount,
        batch_id,
        COUNT(*) OVER (
            PARTITION BY legal_entity, vendor_id,
                         payment_date, currency, payment_amount
        ) AS duplicate_count
    FROM ap_payments
    WHERE payment_status = 'Posted'
)

SELECT
    p.payment_id,
    p.legal_entity,
    p.vendor_id,
    p.payment_date,
    p.payment_amount,
    p.currency,
    p.batch_id,
    s.invoice_id,
    i.invoice_number,
    i.invoice_amount,
    i.po_number,
    s.applied_amount
FROM duplicate_payments p
LEFT JOIN payment_settlements s
    ON p.payment_id = s.payment_id
LEFT JOIN ap_invoices i
    ON s.invoice_id = i.invoice_id
WHERE p.duplicate_count > 1
ORDER BY
    p.legal_entity,
    p.vendor_id,
    p.payment_date,
    p.payment_id,
    s.invoice_id;
