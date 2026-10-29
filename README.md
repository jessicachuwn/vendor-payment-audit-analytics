# Vendor Payment Audit Analytics

**SQL + Python | Internal Audit | Accounts Payable | Risk & Control Testing**

## Project Overview

This project demonstrates a risk-based, data-driven internal audit approach to evaluating vendor payment transactions and identifying potential control exceptions.

It combines SQL, Python, SQLite, and Excel to simulate audit analytics across accounts payable (AP) processes, including duplicate payment detection, invoice-level overpayment analysis, and investigation of payment approval controls.

The project uses synthetic ERP-style transaction data and is intended for audit methodology demonstration and technical skill development.

## Audit Objectives

- Identify potential duplicate vendor payments across payment batches and invoice records.
- Detect invoices with cumulative payment applications exceeding invoice amounts.
- Evaluate payment approval evidence associated with flagged transactions.
- Reconcile payment headers, settlement records, and simulated control totals.
- Document potential exceptions, investigation procedures, and evidence limitations.

## Technology Stack

| Technology | Application |
|---|---|
| SQL / SQLite | Multi-table joins, aggregation, duplicate detection, window functions |
| Python | Data processing, SQL execution, result validation, exception reporting |
| Pandas | Transaction-level analysis and CSV exports |
| Excel | Audit workpapers and exception tracking |
| Git / GitHub | Version control and project documentation |

## Audit Analytics Workflow

**Synthetic ERP Data → SQLite Database → SQL Detection → Python Validation → Exception Investigation → Excel Audit Workpaper**

The analysis incorporates payment headers, invoice records, payment settlements, and payment approvals.

## Key Audit Tests

### AP-003: Duplicate Payment Detection

SQL identifies potential duplicate payments using combinations of legal entity, vendor, payment date, currency, payment amount, and invoice references.

The analysis identified:

- 9 same-day, same-amount payment groups involving 18 payment records.
- 2 groups involving duplicate invoice numbers across distinct invoice IDs.

These are potential exceptions requiring additional investigation; matching payment attributes alone do not establish duplicate disbursements.

### Invoice-Level Overpayment Analysis

SQL aggregates settlement amounts by invoice and compares cumulative applied amounts against original invoice amounts.

The analysis identified two invoice-level overapplication exceptions:

| Legal Entity | Currency | Potential Excess Applied |
|---|---|---:|
| DE01 | EUR | 8,091.69 |
| US02 | USD | 7,141.96 |

One exception involved payments on different dates, demonstrating why same-day duplicate detection alone is insufficient.

These amounts represent potential excess invoice applications within the simulated dataset, not confirmed cash losses.

### Payment Approval Investigation

Flagged transactions are linked to payment approval records to assess:

- Approval status and timing.
- Approval authority and limits.
- Payment creator and approver information.
- Cross-batch processing and potential duplicate-payment prevention gaps.

Recorded approvals do not independently establish that duplicate-payment prevention controls operated effectively.

## Data Reconciliation and Reliability

The simulated V3 dataset includes 50,011 payment records.

Payment headers and settlement records were reconciled, with no missing payments, amount mismatches, or orphan settlements identified in the completed reconciliation.

Because the dataset and control totals are synthetic, these checks establish internal consistency only. They do not independently demonstrate ERP report completeness, IPE reliability, or bank settlement.

## Audit Conclusions and Limitations

The analytics identify transactions for follow-up rather than automatically concluding control deficiencies or financial misstatements.

Further procedures would include inspecting original invoices, bank disbursement evidence, payment approval documentation, ERP duplicate-invoice configurations, override logs, and any subsequent refunds or reversals.

The final assessment would distinguish control design deficiencies, operating effectiveness failures, data issues, and legitimate business transactions.

## Repository Contents

- `sql/` — SQL scripts for duplicate detection and invoice investigation.
- `scripts/` — Python execution and validation scripts.
- `outputs/AP003_SQL_Python_Audit_Workpaper.xlsx` — Audit analytics workpaper.
- `simulation_2026/` — Local synthetic data and SQLite analysis environment; not necessarily included in the public repository.

## Professional Skills Demonstrated

Risk-based audit planning, accounts payable controls, SQL-based transaction testing, Python-assisted audit analytics, exception investigation, data reconciliation, audit documentation, and version control.