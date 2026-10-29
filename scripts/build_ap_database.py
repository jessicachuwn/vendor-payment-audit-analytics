
from pathlib import Path
import argparse
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "demo": {
        "data_dir": ROOT / "simulation_2026" / "demo_data",
        "db_path": ROOT / "simulation_2026" / "ap_audit_demo.db",
    },
    "v3": {
        "data_dir": ROOT / "simulation_2026" / "v3_data",
        "db_path": ROOT / "simulation_2026" / "ap_audit_v3.db",
    },
}

TABLES = {
    "ap_payments": "ap_payments.csv",
    "ap_invoices": "ap_invoices.csv",
    "payment_settlements": "payment_settlements.csv",
    "payment_approvals": "payment_approvals.csv",
}

AMOUNT_COLUMNS = [
    "payment_amount",
    "invoice_amount",
    "applied_amount",
    "approval_limit",
]


def main():
    parser = argparse.ArgumentParser(
        description="Build AP audit SQLite database from synthetic CSV files"
    )
    parser.add_argument(
        "--dataset",
        choices=["demo", "v3"],
        default="v3",
        help="Dataset to import (default: v3)",
    )
    args = parser.parse_args()

    config = DATASETS[args.dataset]
    data_dir = config["data_dir"]
    db_path = config["db_path"]

    missing = [
        filename
        for filename in TABLES.values()
        if not (data_dir / filename).is_file()
    ]

    if missing:
        raise FileNotFoundError(
            f"Missing {args.dataset.upper()} source files: "
            + ", ".join(missing)
        )

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        for table, filename in TABLES.items():
            df = pd.read_csv(
                data_dir / filename,
                dtype=str,
                keep_default_na=False,
            )

            for column in AMOUNT_COLUMNS:
                if column in df.columns:
                    df[column] = pd.to_numeric(
                        df[column],
                        errors="raise",
                    )

            df.to_sql(
                table,
                conn,
                if_exists="replace",
                index=False,
            )

            print(f"{table}: {len(df):,} rows imported")

    print(f"\nDataset: {args.dataset.upper()}")
    print(f"Database ready: {db_path}")


if __name__ == "__main__":
    main()

