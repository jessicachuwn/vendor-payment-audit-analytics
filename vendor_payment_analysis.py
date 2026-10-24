
from pathlib import Path
import pandas as pd

# Define project paths
base_dir = Path(__file__).resolve().parent
data_file = base_dir / "data" / "vendor_payments.csv"
output_dir = base_dir / "outputs"
output_dir.mkdir(exist_ok=True)

# Load population
df = pd.read_csv(data_file)

# Define duplicate detection criteria
duplicate_keys = [
    "vendor_id",
    "invoice_number",
    "amount"
]

# Flag all records in potential duplicate groups
duplicates = df[
    df.duplicated(subset=duplicate_keys, keep=False)
].copy()

# Sort for audit review
duplicates = duplicates.sort_values(
    duplicate_keys + ["payment_date", "payment_id"]
)

# Assign a unique group ID to each potential duplicate
duplicates["duplicate_group"] = (
    duplicates.groupby(duplicate_keys).ngroup() + 1
)

# Number of payments within each group
duplicates["group_payment_count"] = (
    duplicates.groupby(duplicate_keys)["payment_id"]
    .transform("count")
)

# Add review fields
duplicates["audit_status"] = "Pending Review"
duplicates["auditor_comments"] = ""

# Calculate preliminary excess payment exposure
group_summary = (
    duplicates.groupby(
        ["duplicate_group"] + duplicate_keys,
        as_index=False
    )
    .agg(
        payment_count=("payment_id", "count"),
        total_paid=("amount", "sum")
    )
)

group_summary["potential_excess_amount"] = (
    group_summary["total_paid"]
    - group_summary["amount"]
)

# Save audit workbook
output_file = output_dir / "vendor_payment_audit.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df.to_excel(
        writer,
        sheet_name="Population",
        index=False
    )

    duplicates.to_excel(
        writer,
        sheet_name="Duplicate Exceptions",
        index=False
    )

    group_summary.to_excel(
        writer,
        sheet_name="Exception Summary",
        index=False
    )

print("Total population:", len(df))
print("Flagged records:", len(duplicates))
print("Potential duplicate groups:", len(group_summary))
print(
    "Preliminary potential excess amount: $",
    group_summary["potential_excess_amount"].sum()
)
print("Workbook saved to:", output_file)
