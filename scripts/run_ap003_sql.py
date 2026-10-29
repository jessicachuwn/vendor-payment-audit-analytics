
from pathlib import Path
import argparse
import sqlite3
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"

DUPLICATE_SQL = SQL_DIR / "ap003_duplicate_payments.sql"
OVERPAYMENT_SQL = SQL_DIR / "ap003_invoice_overpayment.sql"

DATASETS = {
    "demo": {
        "db": ROOT / "simulation_2026" / "ap_audit_demo.db",
        "output_dir": ROOT / "simulation_2026" / "demo_outputs",
        "expected_records": 6,
        "expected_groups": 3,
        "expected_overpayments": 2,
    },
    "v3": {
        "db": ROOT / "simulation_2026" / "ap_audit_v3.db",
        "output_dir": ROOT / "simulation_2026" / "v3_outputs",
        "expected_records": 18,
        "expected_groups": 9,
        "expected_overpayments": 2,
    },
}

GROUP_KEYS = [
    "legal_entity",
    "vendor_id",
    "payment_date",
    "currency",
    "payment_amount",
]

EXPECTED_OVERPAYMENTS = {
    ("API-0000003", "EUR"): 8091.69,
    ("API-0000004", "USD"): 7141.96,
}


def run_sql(sql_path, conn):
    sql = sql_path.read_text(encoding="utf-8-sig")
    return pd.read_sql_query(sql, conn)


def validate_duplicates(results, config):
    missing = [c for c in GROUP_KEYS if c not in results.columns]
    if missing:
        raise ValueError(f"Duplicate SQL missing columns: {missing}")

    record_count = len(results)
    group_count = results.groupby(GROUP_KEYS, dropna=False).ngroups

    passed = (
        record_count == config["expected_records"]
        and group_count == config["expected_groups"]
    )

    print("\n=== AP-003 DUPLICATE PAYMENT TEST ===")
    print("Matching payment records:", record_count)
    print("Distinct duplicate groups:", group_count)
    print("PASS" if passed else "FAIL", "- Duplicate payment regression")

    return passed


def validate_overpayments(results, config):
    required = ["invoice_id", "currency", "excess_applied"]
    missing = [c for c in required if c not in results.columns]
    if missing:
        raise ValueError(f"Overpayment SQL missing columns: {missing}")

    actual = {
        (str(row.invoice_id), str(row.currency)): round(
            float(row.excess_applied), 2
        )
        for row in results.itertuples(index=False)
    }

    passed = (
        len(results) == config["expected_overpayments"]
        and actual == EXPECTED_OVERPAYMENTS
    )

    print("\n=== AP-003F INVOICE OVERPAYMENT TEST ===")
    print("Potential overapplied invoices:", len(results))
    for (invoice_id, currency), amount in actual.items():
        print(f"{invoice_id} | {currency} | {amount:,.2f}")

    print("PASS" if passed else "FAIL", "- Overpayment regression")

    return passed


def main():
    parser = argparse.ArgumentParser(
        description="AP-003 SQL audit analytics regression runner"
    )
    parser.add_argument(
        "--dataset",
        choices=["demo", "v3"],
        default="v3",
        help="Dataset to analyze (default: v3)",
    )
    args = parser.parse_args()

    config = DATASETS[args.dataset]
    db_path = config["db"]
    output_dir = config["output_dir"]

    if not db_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "Build the selected SQLite database before running."
        )

    with sqlite3.connect(db_path) as conn:
        duplicates = run_sql(DUPLICATE_SQL, conn)
        overpayments = run_sql(OVERPAYMENT_SQL, conn)

    print(f"=== {args.dataset.upper()} AUDIT ANALYTICS ===")

    duplicate_pass = validate_duplicates(duplicates, config)
    overpayment_pass = validate_overpayments(overpayments, config)

    output_dir.mkdir(parents=True, exist_ok=True)

    duplicate_output = output_dir / "AP003_SQL_duplicate_payments.csv"
    overpayment_output = output_dir / "AP003F_SQL_invoice_overpayments.csv"

    duplicates.to_csv(duplicate_output, index=False)
    overpayments.to_csv(overpayment_output, index=False)

    print("\n=== OUTPUT FILES ===")
    print(duplicate_output)
    print(overpayment_output)

    if duplicate_pass and overpayment_pass:
        print("\nPASS - All audit analytics regression tests matched")
    else:
        print("\nFAIL - Audit analytics regression mismatch")
        sys.exit(1)


if __name__ == "__main__":
    main()

