
from pathlib import Path
import sqlite3
import pandas as pd

# Resolve paths relative to the repository, not the terminal location.
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "simulation_2026" / "v3_data"
DB_PATH = ROOT / "simulation_2026" / "ap_audit_v3.db"

TABLES = {
    "ap_payments": "ap_payments.csv",
    "ap_invoices": "ap_invoices.csv",
    "payment_settlements": "payment_settlements.csv",
    "payment_approvals": "payment_approvals.csv",
}

def main():
    missing = [
        filename
        for filename in TABLES.values()
        if not (DATA_DIR / filename).is_file()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing V3 source files: " + ", ".join(missing)
        )

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        for table, filename in TABLES.items():
            source = DATA_DIR / filename
            df = pd.read_csv(source, dtype=str, keep_default_na=False)

            # Preserve identifiers and dates as text.
            # Convert monetary amounts to numeric values.
            for column in (
                "payment_amount",
                "invoice_amount",
                "applied_amount",
                "approval_limit",
            ):
                if column in df.columns:
                    df[column] = pd.to_numeric(
                        df[column], errors="raise"
                    )

            df.to_sql(
                table,
                conn,
                if_exists="replace",
                index=False,
            )

            print(f"{table}: {len(df):,} rows imported")

    print(f"\nDatabase ready: {DB_PATH}")

if __name__ == "__main__":
    main()
