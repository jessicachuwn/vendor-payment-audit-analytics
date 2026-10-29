
from pathlib import Path
import argparse
import sqlite3
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

SQL_PATH = ROOT / "sql" / "ap003_duplicate_payments.sql"

DATASETS = {
    "demo": {
        "db": ROOT / "simulation_2026" / "ap_audit_demo.db",
        "output": ROOT / "simulation_2026" / "demo_outputs"
                  / "AP003_SQL_duplicate_payments.csv",
        "expected_records": 6,
        "expected_groups": 3,
    },
    "v3": {
        "db": ROOT / "simulation_2026" / "ap_audit_v3.db",
        "output": ROOT / "simulation_2026" / "v3_outputs"
                  / "AP003_SQL_duplicate_payments.csv",
        "expected_records": 18,
        "expected_groups": 9,
    },
}

GROUP_KEYS = [
    "legal_entity",
    "vendor_id",
    "payment_date",
    "currency",
    "payment_amount",
]


def main():
    parser = argparse.ArgumentParser(
        description="AP-003 SQL duplicate payment audit analytics"
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
    output_path = config["output"]

    if not db_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "Build the selected SQLite database before running."
        )

    sql = SQL_PATH.read_text(encoding="utf-8-sig")

    with sqlite3.connect(db_path) as conn:
        results = pd.read_sql_query(sql, conn)

    missing_columns = [
        col for col in GROUP_KEYS if col not in results.columns
    ]
    if missing_columns:
        raise ValueError(
            f"SQL result missing columns: {missing_columns}"
        )

    group_count = results.groupby(
        GROUP_KEYS, dropna=False
    ).ngroups

    record_count = len(results)

    print(f"=== AP-003 {args.dataset.upper()} SQL TEST ===")
    print("Matching payment records:", record_count)
    print("Distinct duplicate groups:", group_count)

    passed = (
        record_count == config["expected_records"]
        and group_count == config["expected_groups"]
    )

    if passed:
        print(
            f"PASS - {args.dataset.upper()} "
            "regression baseline matched"
        )
    else:
        print(
            f"REVIEW - Results differ from "
            f"{args.dataset.upper()} regression baseline"
        )
        print(
            "Expected records:",
            config["expected_records"],
        )
        print(
            "Expected groups:",
            config["expected_groups"],
        )

    print("\n=== EXCEPTION DETAILS ===")
    print(results.to_string(index=False))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)

    print("\nOutput:", output_path)

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
