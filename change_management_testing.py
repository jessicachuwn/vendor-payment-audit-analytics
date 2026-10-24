
from pathlib import Path
import pandas as pd

# ============================================================
# 1. File paths and audit scope
# ============================================================

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OUTPUT = BASE / "outputs"
OUTPUT.mkdir(exist_ok=True)

REPORT = OUTPUT / "change_management_audit.xlsx"

PERIOD_START = pd.Timestamp("2026-01-01")
PERIOD_END = pd.Timestamp("2026-01-31")
APPLICATION = "Dynamics AX"

# ============================================================
# 2. Load evidence
# ============================================================

tickets = pd.read_csv(
    DATA / "change_tickets.csv",
    dtype=str,
    keep_default_na=False
)

deployments = pd.read_csv(
    DATA / "production_deployments.csv",
    dtype=str,
    keep_default_na=False
)

access = pd.read_csv(
    DATA / "change_access_matrix.csv",
    dtype=str,
    keep_default_na=False
)

for df in [tickets, deployments, access]:
    for col in df.columns:
        df[col] = df[col].str.strip()

# Check expected schema before testing
required = [
    (tickets, [
        "change_id", "application", "change_type",
        "developer", "approver", "approval_date",
        "uat_status", "uat_date",
        "planned_deployment_date"
    ]),
    (deployments, [
        "deployment_id", "change_id", "application",
        "deployed_by", "deployment_date"
    ]),
    (access, [
        "user_id", "developer_access",
        "change_approval_access",
        "production_deployment_access"
    ])
]

for df, columns in required:
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

# ============================================================
# 3. Basic population integrity
# ============================================================

quality_issues = []

def add_quality_issue(source, record_id, issue):
    quality_issues.append({
        "source": source,
        "record_id": record_id,
        "issue": issue
    })

for name, df, key in [
    ("Change Tickets", tickets, "change_id"),
    ("Deployments", deployments, "deployment_id"),
    ("Access Matrix", access, "user_id")
]:
    for _, row in df[df[key] == ""].iterrows():
        add_quality_issue(name, "", f"Missing {key}")

    for value in df.loc[
        df[key].ne("") & df[key].duplicated(keep=False),
        key
    ].unique():
        add_quality_issue(name, value, f"Duplicate {key}")

# Prevent ambiguous ticket-to-deployment matching
if tickets["change_id"].eq("").any() or \
        tickets["change_id"].duplicated().any():
    raise ValueError(
        "Change ticket IDs must be populated and unique."
    )

if access["user_id"].eq("").any() or \
        access["user_id"].duplicated().any():
    raise ValueError(
        "Access matrix user IDs must be populated and unique."
    )

# ============================================================
# 4. Reconcile deployments to tickets
# ============================================================

deployments["deployment_dt"] = pd.to_datetime(
    deployments["deployment_date"],
    errors="coerce"
)

for _, row in deployments[
    deployments["deployment_dt"].isna()
].iterrows():
    add_quality_issue(
        "Deployments",
        row["deployment_id"],
        "Missing or invalid deployment date"
    )

# Restrict to the requested application and audit period
scope = deployments[
    deployments["application"].eq(APPLICATION)
    & deployments["deployment_dt"].between(
        PERIOD_START, PERIOD_END
    )
].copy()

testing = scope.merge(
    tickets,
    on="change_id",
    how="left",
    suffixes=("_deployment", "_ticket"),
    indicator=True,
    validate="many_to_one"
)

# ============================================================
# 5. Test each production deployment
# ============================================================

exceptions = []
test_results = []

def add_exception(deployment_id, change_id, test, issue):
    exceptions.append({
        "deployment_id": deployment_id,
        "change_id": change_id,
        "test": test,
        "exception": issue,
        "status": "EXCEPTION / FOLLOW-UP"
    })

for _, row in testing.iterrows():

    dep_id = row["deployment_id"]
    change_id = row["change_id"]
    deployed = row["deployment_dt"]

    findings = []

    def flag(test, issue):
        findings.append(test)
        add_exception(dep_id, change_id, test, issue)

    # Ticket traceability
    if row["_merge"] != "both":
        flag(
            "Ticket Traceability",
            "Production deployment has no matching change ticket"
        )

    else:
        # Application consistency
        if row["application_ticket"] != APPLICATION:
            flag(
                "Application Scope",
                "Ticket application does not match deployment"
            )

        change_type = row["change_type"].lower()

        approval = pd.to_datetime(
            row["approval_date"], errors="coerce"
        )
        uat = pd.to_datetime(
            row["uat_date"], errors="coerce"
        )

        if change_type == "normal":

            # Authorization
            if not row["approver"] or pd.isna(approval):
                flag(
                    "Change Authorization",
                    "Approval information is missing"
                )
            elif approval > deployed:
                flag(
                    "Change Authorization",
                    "Approval date is after deployment date"
                )

            # UAT
            if row["uat_status"].lower() != "passed":
                flag(
                    "UAT Testing",
                    "UAT did not pass"
                )
            elif pd.isna(uat):
                flag(
                    "UAT Testing",
                    "UAT completion date is missing"
                )
            elif uat > deployed:
                flag(
                    "UAT Testing",
                    "UAT date is after deployment date"
                )

        elif change_type == "emergency":
            # Emergency approval and retrospective review
            # require additional evidence not in these files.
            flag(
                "Emergency Change Evidence",
                "Emergency authorization and post-"
                "implementation review not independently verified"
            )

        else:
            flag(
                "Change Classification",
                "Unknown or missing change type"
            )

        # Actual deployment performed by developer
        if row["deployed_by"] == row["developer"]:
            flag(
                "Segregation of Duties",
                "Developer performed the production deployment"
            )

    test_results.append({
        "deployment_id": dep_id,
        "change_id": change_id,
        "deployment_date": row["deployment_date"],
        "deployed_by": row["deployed_by"],
        "ticket_found": row["_merge"] == "both",
        "exception_count": len(findings),
        "result": (
            "FOLLOW-UP REQUIRED"
            if findings else
            "NO EXCEPTION IDENTIFIED"
        )
    })

# ============================================================
# 6. Access conflict review
# ============================================================

access_review = access.copy()

for col in [
    "developer_access",
    "change_approval_access",
    "production_deployment_access"
]:
    access_review[col] = (
        access_review[col].str.lower().eq("yes")
    )

access_review["dev_deploy_conflict"] = (
    access_review["developer_access"]
    & access_review["production_deployment_access"]
)

access_review["dev_approve_conflict"] = (
    access_review["developer_access"]
    & access_review["change_approval_access"]
)

access_review["approve_deploy_conflict"] = (
    access_review["change_approval_access"]
    & access_review["production_deployment_access"]
)

access_review["access_review_result"] = (
    access_review[
        [
            "dev_deploy_conflict",
            "dev_approve_conflict",
            "approve_deploy_conflict"
        ]
    ].any(axis=1).map({
        True: "POTENTIAL SOD CONFLICT",
        False: "NO CONFLICT IDENTIFIED"
    })
)

# ============================================================
# 7. Identify tickets without a recorded deployment
# ============================================================

ticket_reconciliation = tickets[
    ["change_id", "application", "change_type"]
].copy()

ticket_reconciliation["deployment_count"] = (
    ticket_reconciliation["change_id"].map(
        scope["change_id"].value_counts()
    ).fillna(0).astype(int)
)

ticket_reconciliation["status"] = (
    ticket_reconciliation["deployment_count"]
    .map(
        lambda n: (
            "NO IN-SCOPE DEPLOYMENT - INVESTIGATE STATUS"
            if n == 0 else
            "DEPLOYMENT IDENTIFIED"
        )
    )
)

# ============================================================
# 8. Audit summary and limitations
# ============================================================

exception_df = pd.DataFrame(
    exceptions,
    columns=[
        "deployment_id", "change_id", "test",
        "exception", "status"
    ]
)

quality_df = pd.DataFrame(
    quality_issues,
    columns=["source", "record_id", "issue"]
)

results_df = pd.DataFrame(test_results)

summary = pd.DataFrame([
    ["Change tickets supplied", len(tickets)],
    ["In-scope production deployments", len(scope)],
    ["Deployments requiring follow-up",
     int((results_df["exception_count"] > 0).sum())],
    ["Exception flags", len(exception_df)],
    ["Potential access conflicts",
     int((access_review["access_review_result"]
          == "POTENTIAL SOD CONFLICT").sum())],
    ["Population quality flags", len(quality_df)]
], columns=["metric", "value"])

limitations = pd.DataFrame({
    "limitation": [
        "All source records are simulated.",
        "Independent population completeness is not established.",
        "CSV approval dates do not prove approval authenticity.",
        "Date-only fields cannot prove sequence within a day.",
        "UAT status is not independently supported by test evidence.",
        "Emergency authorization and retrospective review "
        "are not evidenced in the supplied fields.",
        "Access matrix does not prove effective production "
        "permissions or compensating controls.",
        "A ticket without a deployment is not automatically "
        "a control failure.",
        "No actual Dynamics AX report change has been linked "
        "to the Step 7 simulated join defect."
    ]
})

# ============================================================
# 9. Export workpaper
# ============================================================

with pd.ExcelWriter(REPORT, engine="openpyxl") as writer:
    summary.to_excel(
        writer, "Audit Summary", index=False
    )
    results_df.to_excel(
        writer, "Deployment Testing", index=False
    )
    exception_df.to_excel(
        writer, "Audit Exceptions", index=False
    )
    access_review.to_excel(
        writer, "Access Review", index=False
    )
    ticket_reconciliation.to_excel(
        writer, "Ticket Reconciliation", index=False
    )
    quality_df.to_excel(
        writer, "Data Quality", index=False
    )
    limitations.to_excel(
        writer, "Audit Limitations", index=False
    )

print("\nITGC Change Management Testing Complete")
print(summary.to_string(index=False))
print("\nWorkpaper saved to:", REPORT)
print(
    "Audit conclusion: FOLLOW-UP REQUIRED; "
    "CONTROL EFFECTIVENESS NOT ESTABLISHED"
)
