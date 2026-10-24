
from pathlib import Path
import pandas as pd

# ---------------------------------------
# 1. Define file paths
# ---------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

PAYMENT_FILE = DATA_DIR / "vendor_payments.csv"
CONTROL_FILE = DATA_DIR / "ap_control_totals.csv"
REPORT_FILE = OUTPUT_DIR / "population_validation_workpaper.xlsx"

# ---------------------------------------
# 2. Load source data
# ---------------------------------------
payments = pd.read_csv(PAYMENT_FILE, dtype=str)
controls = pd.read_csv(CONTROL_FILE)

required_columns = [
    "payment_id",
    "vendor_id",
    "vendor_name",
    "invoice_number",
    "payment_date",
    "amount"
]

missing_columns = [
    col for col in required_columns
    if col not in payments.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

if len(controls) != 1:
    raise ValueError(
        "Expected exactly one control totals record."
    )

# ---------------------------------------
# 3. Normalize and validate fields
# ---------------------------------------
payments["amount_numeric"] = pd.to_numeric(
    payments["amount"], errors="coerce"
)

payments["payment_date_parsed"] = pd.to_datetime(
    payments["payment_date"],
    errors="coerce"
)

period_start = pd.Timestamp(
    controls.loc[0, "period_start"]
)
period_end = pd.Timestamp(
    controls.loc[0, "period_end"]
)

exceptions = []

def flag_exception(mask, issue):
    for _, record in payments.loc[mask].iterrows():
        exceptions.append({
            "payment_id": record["payment_id"],
            "exception_type": issue,
            "audit_status": "Pending Review"
        })

# Missing critical identifiers
for col in ["payment_id", "vendor_id", "invoice_number"]:
    blank = (
        payments[col].isna()
        | payments[col].str.strip().eq("")
    )
    flag_exception(blank, f"Missing {col}")

# Duplicate unique payment identifiers
flag_exception(
    payments["payment_id"].notna()
    & payments["payment_id"].duplicated(keep=False),
    "Duplicate payment ID"
)

# Invalid amounts
flag_exception(
    payments["amount_numeric"].isna(),
    "Invalid amount"
)

# Non-positive amounts (requires business review)
flag_exception(
    payments["amount_numeric"].le(0),
    "Non-positive amount - review transaction type"
)

# Invalid dates
flag_exception(
    payments["payment_date_parsed"].isna(),
    "Invalid payment date"
)

# Out-of-period transactions
flag_exception(
    payments["payment_date_parsed"].notna()
    & ~payments["payment_date_parsed"].between(
        period_start, period_end
    ),
    "Payment outside audit period"
)

exception_df = pd.DataFrame(
    exceptions,
    columns=[
        "payment_id",
        "exception_type",
        "audit_status"
    ]
)

# ---------------------------------------
# 4. Reconcile to independent totals
# ---------------------------------------
actual_count = len(payments)
actual_amount = payments["amount_numeric"].sum()

expected_count = int(controls.loc[0, "record_count"])
expected_amount = float(
    controls.loc[0, "total_amount"]
)

count_difference = actual_count - expected_count
amount_difference = actual_amount - expected_amount

count_pass = count_difference == 0
amount_pass = (
    payments["amount_numeric"].notna().all()
    and abs(amount_difference) < 0.005
)

reconciliation = pd.DataFrame([
    {
        "metric": "Record Count",
        "source_total": expected_count,
        "extracted_total": actual_count,
        "difference": count_difference,
        "status": "PASS" if count_pass else "FAIL"
    },
    {
        "metric": "Payment Amount",
        "source_total": expected_amount,
        "extracted_total": actual_amount,
        "difference": amount_difference,
        "status": "PASS" if amount_pass else "FAIL"
    }
])

# ---------------------------------------
# 5. Prepare population summary
# ---------------------------------------
summary = pd.DataFrame([
    {"metric": "Population Records",
     "value": actual_count},
    {"metric": "Total Payment Amount",
     "value": actual_amount},
    {"metric": "Unique Payment IDs",
     "value": payments["payment_id"].nunique()},
    {"metric": "Data Quality Exception Flags",
     "value": len(exception_df)},
    {"metric": "Audit Period Start",
     "value": str(period_start.date())},
    {"metric": "Audit Period End",
     "value": str(period_end.date())}
])

# ---------------------------------------
# 6. Prepare accuracy testing sample
# ---------------------------------------
sample_size = min(5, len(payments))

sample = payments.sample(
    n=sample_size,
    random_state=42
)[required_columns].copy()

sample["source_evidence_reference"] = ""
sample["field_accuracy_result"] = "Not Tested"
sample["auditor_comments"] = ""

# ---------------------------------------
# 7. Prepare audit conclusion
# ---------------------------------------
recon_pass = count_pass and amount_pass
quality_pass = exception_df.empty

conclusion = pd.DataFrame([
    {
        "test": "Control Total Reconciliation",
        "result": "PASS" if recon_pass else "FAIL",
        "limitation": (
            "Control totals are simulated; "
            "independent ERP evidence is required."
        )
    },
    {
        "test": "Data Quality",
        "result": "PASS" if quality_pass else "REVIEW",
        "limitation": (
            "Automated checks do not establish "
            "source-system accuracy."
        )
    },
    {
        "test": "Field Accuracy",
        "result": "NOT TESTED",
        "limitation": (
            "Selected samples require comparison "
            "to independent source evidence."
        )
    }
])

# ---------------------------------------
# 8. Generate audit workbook
# ---------------------------------------
with pd.ExcelWriter(
    REPORT_FILE, engine="openpyxl"
) as writer:

    summary.to_excel(
        writer,
        sheet_name="Population Summary",
        index=False
    )

    reconciliation.to_excel(
        writer,
        sheet_name="Reconciliation",
        index=False
    )

    exception_df.to_excel(
        writer,
        sheet_name="Data Quality Exceptions",
        index=False
    )

    sample.to_excel(
        writer,
        sheet_name="Field Accuracy Sample",
        index=False
    )

    conclusion.to_excel(
        writer,
        sheet_name="Audit Conclusion",
        index=False
    )

print("Population records:", actual_count)
print("Total amount:", actual_amount)
print("Record count reconciliation:",
      "PASS" if count_pass else "FAIL")
print("Amount reconciliation:",
      "PASS" if amount_pass else "FAIL")
print("Data quality exception flags:", len(exception_df))
print("Field accuracy testing: NOT TESTED")
print("Workpaper saved to:", REPORT_FILE)
