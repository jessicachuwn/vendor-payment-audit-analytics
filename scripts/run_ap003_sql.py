from pathlib import Path
import sqlite3
import pandas as pd

db_path = Path("simulation_2026/ap_audit_v3.db")
sql_path = Path("sql/ap003_duplicate_payments.sql")
output_path = Path(
    "simulation_2026/v3_outputs/AP003_SQL_duplicate_payments.csv"
)

if not db_path.exists():
    raise FileNotFoundError(
        "Database not found. Run the SQLite import step first."
    )

sql = sql_path.read_text(encoding="utf-8-sig")

with sqlite3.connect(db_path) as conn:
    results = pd.read_sql_query(sql, conn)

group_keys = [
    "legal_entity",
    "vendor_id",
    "payment_date",
    "currency",
    "payment_amount"
]

group_count = results.groupby(group_keys).ngroups

print("=== AP-003 SQL + PYTHON VALIDATION ===")
print("Matching payment records:", len(results))
print("Distinct duplicate groups:", group_count)

expected_records = 18
expected_groups = 9

if len(results) == expected_records and group_count == expected_groups:
    print("PASS - SQL results match previous Python test")
else:
    print("REVIEW - SQL results differ from previous Python test")

print("\n=== EXCEPTION DETAILS ===")
print(results.to_string(index=False))

output_path.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(output_path, index=False)

print("\nOutput:", output_path)
