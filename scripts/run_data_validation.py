
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import argparse
import sqlite3
import sys

import pandas as pd


# ============================================================
# DV-001 Population Reconciliation
# Source CSV vs SQLite Database
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

TABLES = {
    "ap_payments": {
        "filename": "ap_payments.csv",
        "amount_column": "payment_amount",
    },
    "ap_invoices": {
        "filename": "ap_invoices.csv",
        "amount_column": "invoice_amount",
    },
    "payment_settlements": {
        "filename": "payment_settlements.csv",
        "amount_column": "applied_amount",
    },
}

GROUP_COLUMNS = ["legal_entity", "currency"]


def amount_to_cents(value):
    """Convert monetary amount to integer cents."""
    amount = Decimal(str(value))
    return int(
        (amount * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def source_summary(csv_path, amount_column):
    """Summarize source CSV by entity and currency."""

    df = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False,
    )

    required = GROUP_COLUMNS + [amount_column]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            "Missing source columns: {}".format(missing)
        )

    df["amount_cents"] = df[amount_column].apply(
        amount_to_cents
    )

    summary = (
        df.groupby(GROUP_COLUMNS, dropna=False)
        .agg(
            record_count=("amount_cents", "size"),
            total_amount_cents=("amount_cents", "sum"),
        )
        .reset_index()
    )

    return summary


def database_summary(conn, table_name, amount_column):
    """Summarize SQLite records using DV-001 SQL."""

    allowed_tables = {
        table: config["amount_column"]
        for table, config in TABLES.items()
    }

    if allowed_tables.get(table_name) != amount_column:
        raise ValueError("Invalid table or amount column")

    sql_path = (
        ROOT
        / "sql"
        / "validation"
        / "dv001_population_summary.sql"
    )

    sql_template = sql_path.read_text(encoding="utf-8-sig")

    sql = sql_template.format(
        table_name=table_name,
        amount_column=amount_column,
    )

    return pd.read_sql_query(sql, conn)


def reconcile_table(
    conn,
    csv_path,
    table_name,
    amount_column,
):
    """Compare source and database grouped totals."""

    csv_summary = source_summary(
        csv_path,
        amount_column,
    )

    db_summary = database_summary(
        conn,
        table_name,
        amount_column,
    )

    comparison = csv_summary.merge(
        db_summary,
        on=GROUP_COLUMNS,
        how="outer",
        suffixes=("_csv", "_db"),
        indicator=True,
    )

    count_equal = (
        comparison["record_count_csv"]
        == comparison["record_count_db"]
    )

    amount_equal = (
        comparison["total_amount_cents_csv"]
        == comparison["total_amount_cents_db"]
    )

    comparison["status"] = "FAIL"

    comparison.loc[
        (comparison["_merge"] == "both")
        & count_equal
        & amount_equal,
        "status",
    ] = "PASS"

    comparison.insert(0, "table_name", table_name)

    return comparison


def classify_exception(row):
    """Classify reconciliation exceptions."""

    if row["_merge"] != "both":
        return "MISSING_POPULATION_GROUP"

    count_diff = row["record_count_difference"]
    amount_diff = row["amount_difference"]

    if count_diff != 0 and amount_diff != 0:
        return "COUNT_AND_AMOUNT_MISMATCH"

    if count_diff != 0:
        return "COUNT_MISMATCH"

    if amount_diff != 0:
        return "AMOUNT_MISMATCH"

    return "NONE"


def validate(dataset):
    """Execute DV-001 and produce the audit report."""

    if dataset not in ("demo", "v3"):
        raise ValueError("Invalid dataset: {}".format(dataset))

    base_dir = ROOT / "simulation_2026"

    data_dir = base_dir / (
        "demo_data" if dataset == "demo" else "v3_data"
    )

    db_path = base_dir / (
        "ap_audit_demo.db"
        if dataset == "demo"
        else "ap_audit_v3.db"
    )

    output_dir = base_dir / (
        "demo_outputs"
        if dataset == "demo"
        else "v3_outputs"
    )

    if not db_path.is_file():
        raise FileNotFoundError(
            "Database not found: {}".format(db_path)
        )

    results = []

    with sqlite3.connect(str(db_path)) as conn:
        for table_name, config in TABLES.items():
            csv_path = data_dir / config["filename"]

            if not csv_path.is_file():
                raise FileNotFoundError(
                    "Source CSV not found: {}".format(csv_path)
                )

            comparison = reconcile_table(
                conn,
                csv_path,
                table_name,
                config["amount_column"],
            )

            results.append(comparison)

    summary = pd.concat(
        results,
        ignore_index=True,
    )

    # --------------------------------------------------------
    # Exception Report Enhancement
    # --------------------------------------------------------

    summary.insert(0, "test_id", "DV-001")

    summary["record_count_difference"] = (
        summary["record_count_csv"].fillna(0)
        - summary["record_count_db"].fillna(0)
    )

    summary["amount_difference"] = (
        summary["total_amount_cents_csv"].fillna(0)
        - summary["total_amount_cents_db"].fillna(0)
    ) / 100

    summary["exception_type"] = summary.apply(
        classify_exception,
        axis=1,
    )

    summary["investigation_status"] = (
        summary["status"].map({
            "PASS": "NOT_REQUIRED",
            "FAIL": "PENDING_INVESTIGATION",
        })
    )

    # --------------------------------------------------------
    # Save Audit Workpaper
    # --------------------------------------------------------

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        output_dir
        / "DV001_population_reconciliation.csv"
    )

    summary.to_csv(
        report_path,
        index=False,
    )

    # --------------------------------------------------------
    # Print Results
    # --------------------------------------------------------

    print("\n=== DV-001 POPULATION RECONCILIATION ===\n")

    print(
        summary.to_string(index=False)
    )

    total_groups = len(summary)
    failed_groups = int(
        (summary["status"] == "FAIL").sum()
    )
    passed_groups = total_groups - failed_groups

    print("\n=== VALIDATION SUMMARY ===")
    print("Total groups:", total_groups)
    print("Passed groups:", passed_groups)
    print("Failed groups:", failed_groups)

    print("\nReport:", report_path)

    if failed_groups == 0:
        print("\nPASS - DV-001 Population Reconciliation")
        return 0

    print("\nFAIL - DV-001 Population Reconciliation")
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="DV-001 Population Reconciliation"
    )

    parser.add_argument(
        "--dataset",
        choices=["demo", "v3"],
        default="demo",
    )

    args = parser.parse_args()

    sys.exit(validate(args.dataset))


if __name__ == "__main__":
    main()
