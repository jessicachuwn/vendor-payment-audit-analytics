-- AP-003F: Invoice Overpayment Analysis

SELECT
    i.invoice_id,
    i.invoice_number,
    i.legal_entity,
    i.vendor_id,
    i.currency,
    i.invoice_amount,
    COUNT(DISTINCT p.payment_id) AS payment_count,
    ROUND(SUM(s.applied_amount), 2) AS total_applied,
    ROUND(SUM(s.applied_amount) - i.invoice_amount, 2) AS excess_applied
FROM ap_invoices i
JOIN payment_settlements s
    ON i.invoice_id = s.invoice_id
JOIN ap_payments p
    ON s.payment_id = p.payment_id
WHERE p.payment_status = 'Posted'
GROUP BY
    i.invoice_id,
    i.invoice_number,
    i.legal_entity,
    i.vendor_id,
    i.currency,
    i.invoice_amount
HAVING ROUND(SUM(s.applied_amount) - i.invoice_amount, 2) > 0
ORDER BY excess_applied DESC;
