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

The audit findings summarized below are based on the full V3 synthetic simulation dataset, which is maintained locally. The publicly available Demo dataset provides a smaller, reproducible subset of the duplicate-payment analysis (3 potential duplicate groups involving 6 payment records). The full V3 results and invoice-level overapplication findings are documented for methodology demonstration but cannot be independently reproduced from the public Demo dataset alone.

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

## How to Run

### Quick Start — Reproducible Demo

This repository includes a small synthetic ERP dataset for demonstrating the AP-003 duplicate payment audit test.

**Prerequisites:** Python 3.10 or later and pandas.

From the repository root:

```bash
python -m pip install pandas
python scripts/build_ap_database.py --dataset demo
python scripts/run_ap003_sql.py --dataset demo
```

**Expected regression results:**

```text
Matching payment records: 6
Distinct duplicate groups: 3
PASS - DEMO regression baseline matched
```

The demo dataset contains 30 payments, 32 invoices, 34 settlement records, and 30 approval records.

The resulting exception report is saved to:

`simulation_2026/demo_outputs/AP003_SQL_duplicate_payments.csv`

The six matching payment records represent three potential duplicate-payment groups, not six confirmed duplicate disbursements.

### Full V3 Simulation

The larger V3 synthetic dataset is maintained locally and is not distributed with this repository.

To run the full V3 analysis after obtaining the required synthetic source CSV files:

```bash
python scripts/build_ap_database.py --dataset v3
python scripts/run_ap003_sql.py --dataset v3
```

The V3 regression baseline is 18 matching payment records across 9 groups.

### Audit Workpaper

The audit workpaper is available at:

`outputs/AP003_SQL_Python_Audit_Workpaper.xlsx`

It documents the audit methodology, exception investigation, potential overapplications, and evidence limitations.

### Scope and Limitations

- The demo uses synthetic ERP-style data, not real vendor or bank transactions.
- Regression checks compare SQL results against fixed dataset-specific baselines; they are not independent audit evidence.
- Potential duplicate-payment exceptions require invoice, settlement, approval, and bank evidence before concluding a control deficiency or financial loss.
- Additional SQL investigation scripts are provided for review but are not yet integrated into the automated Python runner.
- Rebuilding a database replaces the four corresponding SQLite tables.