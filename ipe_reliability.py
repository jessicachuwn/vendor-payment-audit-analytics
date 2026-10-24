
from pathlib import Path
import pandas as pd

# =========================================
# IPE Reliability Testing
# Vendor Payment Audit Analytics
# =========================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

METADATA_FILE = DATA_DIR / "ipe_report_metadata.csv"
CONTROL_FILE = DATA_DIR / "ap_control_totals.csv"
PAYMENT_FILE = DATA_DIR / "vendor_payments.csv"

REPORT_FILE = OUTPUT_DIR / "ipe_reliability_workpaper.xlsx"

# 1. Define expected audit scope
EXPECTED_SCOPE = {
    "report_name": "AP Payment Detail",
    "source_system": "Dynamics AX",
    "legal_entity": "US01",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "payment_status": "Posted",
    "report_type": "Standard ERP Report"
}

# 2. Read report metadata
metadata = pd.read_csv(
    METADATA_FILE,
    dtype=str,
    keep_default_na=False
)

if len(metadata) != 1:
    raise ValueError(
        "Expected exactly one metadata record."
    )

# 3. Validate report parameters
parameter_results = []

for field, expected in EXPECTED_SCOPE.items():
    actual = metadata.loc[0, field]

    parameter_results.append({
        "parameter": field,
        "expected_value": expected,
        "reported_value": actual,
        "comparison_result": (
            "MATCH" if actual == expected else "MISMATCH"
        ),
        "source_evidence_status": "NOT VERIFIED",
        "auditor_comments": ""
    })

parameter_df = pd.DataFrame(parameter_results)

# 4. Check population totals
payments = pd.read_csv(PAYMENT_FILE)
controls = pd.read_csv(CONTROL_FILE)

if len(controls) != 1:
    raise ValueError(
        "Expected exactly one control totals record."
    )

payments["amount"] = pd.to_numeric(
    payments["amount"], errors="coerce"
)

actual_count = len(payments)
actual_amount = payments["amount"].sum()

expected_count = int(controls.loc[0, "record_count"])
expected_amount = float(
    controls.loc[0, "total_amount"]
)

count_match = actual_count == expected_count
amount_match = (
    payments["amount"].notna().all()
    and abs(actual_amount - expected_amount) < 0.005
)

reconciliation_df = pd.DataFrame([
    {
        "test": "Record Count Reconciliation",
        "expected": expected_count,
        "actual": actual_count,
        "result": "MATCH" if count_match else "MISMATCH",
        "evidence_status": "SIMULATED"
    },
    {
        "test": "Payment Amount Reconciliation",
        "expected": expected_amount,
        "actual": actual_amount,
        "result": "MATCH" if amount_match else "MISMATCH",
        "evidence_status": "SIMULATED"
    }
])

# 5. Identify evidence requirements
evidence_df = pd.DataFrame([
    {
        "area": "Report Parameters",
        "required_evidence": (
            "ERP report parameter screenshot or "
            "system-generated execution log"
        ),
        "status": "NOT TESTED",
        "auditor_comments": ""
    },
    {
        "area": "Report Logic",
        "required_evidence": (
            "Report definition, query logic, "
            "field mapping, and filtering rules"
        ),
        "status": "NOT TESTED",
        "auditor_comments": ""
    },
    {
        "area": "Report Completeness",
        "required_evidence": (
            "Independent ERP control totals "
            "and source-to-report reconciliation"
        ),
        "status": "NOT TESTED",
        "auditor_comments": ""
    },
    {
        "area": "Field Accuracy",
        "required_evidence": (
            "Sampled ERP source transactions "
            "and supporting payment records"
        ),
        "status": "NOT TESTED",
        "auditor_comments": ""
    },
    {
        "area": "ITGC Dependencies",
        "required_evidence": (
            "Relevant access and change "
            "management control evidence"
        ),
        "status": "NOT TESTED",
        "auditor_comments": ""
    }
])

# 6. Record important scope limitations
limitations_df = pd.DataFrame([
    {
        "limitation": "Metadata source",
        "description": (
            "Metadata is manually supplied "
            "and has not been authenticated "
            "against the ERP."
        )
    },
    {
        "limitation": "Missing transaction fields",
        "description": (
            "Payment population lacks legal_entity "
            "and payment_status columns. "
            "Record-level scope cannot be verified."
        )
    },
    {
        "limitation": "Simulated control totals",
        "description": (
            "Control totals are simulated "
            "and are not independent ERP evidence."
        )
    },
    {
        "limitation": "Source accuracy",
        "description": (
            "No source-system transaction "
            "comparison has been performed."
        )
    }
])

# 7. Determine preliminary status
parameter_match = (
    parameter_df["comparison_result"].eq("MATCH").all()
)

automated_checks_pass = (
    parameter_match and count_match and amount_match
)

conclusion_df = pd.DataFrame([
    {
        "area": "Automated Consistency Checks",
        "result": (
            "PASS" if automated_checks_pass else "FAIL"
        ),
        "conclusion": (
            "Metadata and totals are internally "
            "consistent with expected values."
            if automated_checks_pass else
            "One or more consistency checks failed."
        )
    },
    {
        "area": "IPE Reliability",
        "result": "NOT ESTABLISHED",
        "conclusion": (
            "Requires authenticated report parameters, "
            "report logic review, source accuracy testing, "
            "and evaluation of relevant IT controls."
        )
    }
])

# 8. Generate Excel workpaper
with pd.ExcelWriter(
    REPORT_FILE,
    engine="openpyxl"
) as writer:

    parameter_df.to_excel(
        writer,
        sheet_name="Parameter Testing",
        index=False
    )

    reconciliation_df.to_excel(
        writer,
        sheet_name="Reconciliation",
        index=False
    )

    evidence_df.to_excel(
        writer,
        sheet_name="Evidence Checklist",
        index=False
    )

    limitations_df.to_excel(
        writer,
        sheet_name="Limitations",
        index=False
    )

    conclusion_df.to_excel(
        writer,
        sheet_name="Audit Conclusion",
        index=False
    )

print("IPE Reliability Testing Complete")
print("Parameter comparisons:",
      "MATCH" if parameter_match else "MISMATCH")
print("Record count:",
      "MATCH" if count_match else "MISMATCH")
print("Payment amount:",
      "MATCH" if amount_match else "MISMATCH")
print("IPE Reliability: NOT ESTABLISHED")
print("Workpaper saved to:", REPORT_FILE)
