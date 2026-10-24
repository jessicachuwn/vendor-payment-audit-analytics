
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Simulated payment source records
payments = pd.DataFrame([
    ["P001", "V001", "US01", 1500],
    ["P002", "V002", "US01", 2200],
    ["P003", "V003", "US01", 850],
    ["P004", "V001", "US01", 3400],
], columns=[
    "payment_id", "vendor_id",
    "legal_entity", "amount"
])

# Simulated vendor master records
vendors = pd.DataFrame([
    ["V001", "US01", "ABC Supplies"],
    ["V002", "US01", "XYZ Logistics"],
    ["V001", "US02", "ABC International"],
], columns=[
    "vendor_id", "legal_entity",
    "vendor_name"
])

# Incorrect join: vendor_id only
incorrect = payments.merge(
    vendors,
    on="vendor_id",
    how="inner"
)

# Corrected join: vendor_id + legal_entity
corrected = payments.merge(
    vendors,
    on=["vendor_id", "legal_entity"],
    how="left",
    validate="many_to_one",
    indicator=True
)

# Identify unmatched source payments
unmatched = corrected[
    corrected["_merge"] == "left_only"
].copy()

# Compare record counts and amounts
summary = pd.DataFrame([
    {
        "scenario": "Source Payment Population",
        "record_count": len(payments),
        "total_amount": payments["amount"].sum()
    },
    {
        "scenario": "Incorrect Join",
        "record_count": len(incorrect),
        "total_amount": incorrect["amount"].sum()
    },
    {
        "scenario": "Corrected Join",
        "record_count": len(corrected),
        "total_amount": corrected["amount"].sum()
    }
])

# Generate audit workpaper
report_file = (
    OUTPUT_DIR / "report_logic_review.xlsx"
)

with pd.ExcelWriter(
    report_file,
    engine="openpyxl"
) as writer:
    payments.to_excel(
        writer, "Source Payments", index=False
    )
    vendors.to_excel(
        writer, "Vendor Master", index=False
    )
    incorrect.to_excel(
        writer, "Incorrect Join", index=False
    )
    corrected.to_excel(
        writer, "Corrected Join", index=False
    )
    unmatched.to_excel(
        writer, "Unmatched Payments", index=False
    )
    summary.to_excel(
        writer, "Reconciliation", index=False
    )

print(summary.to_string(index=False))
print("Unmatched payments:", len(unmatched))
print("Workpaper saved to:", report_file)
