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

## How to Run

### Prerequisites

- Python 3.10 or later
- pandas
- SQLite (accessed through Python's built-in `sqlite3` module)

Install the required Python package:

```bash
python -m pip install pandas
```

### Data Setup

This project uses synthetic ERP-style accounts payable data.

The V3 source CSV files are stored locally and are not currently distributed with the GitHub repository.

To run the AP-003 analysis, place the following files in `simulation_2026/v3_data/`:

- `ap_payments.csv`
- `ap_invoices.csv`
- `payment_settlements.csv`
- `payment_approvals.csv`

### Step 1: Build the SQLite Database

From the repository root, run:

```bash
python scripts/build_ap_database.py
```

This imports the four CSV files into `simulation_2026/ap_audit_v3.db`.

**Note:** Re-running this script replaces the four corresponding SQLite tables.

### Step 2: Run AP-003 Duplicate Payment Detection

```bash
python scripts/run_ap003_sql.py
```

The script executes `sql/ap003_duplicate_payments.sql`, counts potential duplicate payment groups, compares the results against the fixed V3 regression baseline, and exports a CSV exception report.

### Step 3: Review the Results

The exception report is saved to:

`simulation_2026/v3_outputs/AP003_SQL_duplicate_payments.csv`

The audit workpaper is available at:

`outputs/AP003_SQL_Python_Audit_Workpaper.xlsx`

### Reproducibility Limitations

The fixed regression baseline of 18 payment records across 9 groups applies only to the original V3 synthetic dataset.

The other SQL investigation scripts are available for review, but they are not yet integrated into the automated Python runner.

The repository does not currently contain all input data required for an independent end-to-end execution. No real vendor, banking, or confidential ERP information is used.