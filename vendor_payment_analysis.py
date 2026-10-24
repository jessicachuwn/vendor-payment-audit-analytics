
from pathlib import Path
import pandas as pd

# Project folders
base_dir = Path(__file__).resolve().parent
data_file = base_dir / "data" / "vendor_payments.csv"
output_dir = base_dir / "outputs"
output_dir.mkdir(exist_ok=True)

# Load the AP payment population
df = pd.read_csv(data_file)

# Identify potential duplicate payments
duplicate_keys = ["vendor_id", "invoice_number", "amount"]

duplicates = df[
    df.duplicated(subset=duplicate_keys, keep=False)
].copy()

duplicates = duplicates.sort_values(duplicate_keys)

# Export exceptions for auditor review
output_file = output_dir / "duplicate_payment_exceptions.xlsx"

duplicates.to_excel(output_file, index=False)

print("Total payment records:", len(df))
print("Potential duplicate payment records:", len(duplicates))
print("Exception report saved to:", output_file)
