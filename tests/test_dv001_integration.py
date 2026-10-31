
import importlib.util
import shutil
import sqlite3
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def dv001_environment(tmp_path, monkeypatch):
    # 1. Create an isolated project structure.
    source_dir = (
        PROJECT_ROOT / "simulation_2026" / "demo_data"
    )
    target_dir = (
        tmp_path / "simulation_2026" / "demo_data"
    )
    target_dir.mkdir(parents=True)

    for filename in [
        "ap_payments.csv",
        "ap_invoices.csv",
        "payment_settlements.csv",
    ]:
        shutil.copy2(
            source_dir / filename,
            target_dir / filename,
        )

    # 2. Copy the working Demo database.
    db_path = (
        tmp_path / "simulation_2026" / "ap_audit_demo.db"
    )
    shutil.copy2(
        PROJECT_ROOT
        / "simulation_2026"
        / "ap_audit_demo.db",
        db_path,
    )

    # 3. Copy the DV-001 SQL template.
    sql_dir = tmp_path / "sql" / "validation"
    sql_dir.mkdir(parents=True)

    shutil.copy2(
        PROJECT_ROOT
        / "sql"
        / "validation"
        / "dv001_population_summary.sql",
        sql_dir / "dv001_population_summary.sql",
    )

    # 4. Load the actual DV-001 Python runner.
    script_path = (
        PROJECT_ROOT / "scripts" / "run_data_validation.py"
    )

    spec = importlib.util.spec_from_file_location(
        "dv001_runner", script_path
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    # Redirect the runner to the temporary project.
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    return runner, db_path, tmp_path


def test_dv001_passes_with_matching_data(dv001_environment):
    runner, db_path, root = dv001_environment

    result = runner.validate("demo")

    assert result == 0

    report_path = (
        root
        / "simulation_2026"
        / "demo_outputs"
        / "DV001_population_reconciliation.csv"
    )

    assert report_path.exists()

    report = pd.read_csv(report_path)
    assert len(report) == 15
    assert report["status"].eq("PASS").all()


def test_dv001_fails_on_amount_difference(dv001_environment):
    runner, db_path, root = dv001_environment

    # Deliberately increase one payment by USD 1.00.
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            UPDATE ap_payments
            SET payment_amount = payment_amount + 1.00
            WHERE payment_id = (
                SELECT payment_id
                FROM ap_payments
                WHERE currency = 'USD'
                LIMIT 1
            )
        """)

    result = runner.validate("demo")

    assert result == 1

    report_path = (
        root
        / "simulation_2026"
        / "demo_outputs"
        / "DV001_population_reconciliation.csv"
    )

    report = pd.read_csv(report_path)

    assert report["status"].eq("FAIL").any()

    failed = report[report["status"] == "FAIL"]

    assert (
        failed["total_amount_cents_csv"]
        != failed["total_amount_cents_db"]
    ).any()


def test_dv001_fails_on_missing_record(dv001_environment):
    runner, db_path, root = dv001_environment

    # Deliberately delete one settlement from the DB copy.
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            DELETE FROM payment_settlements
            WHERE rowid = (
                SELECT rowid
                FROM payment_settlements
                LIMIT 1
            )
        """)

    result = runner.validate("demo")

    assert result == 1

    report_path = (
        root
        / "simulation_2026"
        / "demo_outputs"
        / "DV001_population_reconciliation.csv"
    )

    report = pd.read_csv(report_path)

    assert report["status"].eq("FAIL").any()

    failed = report[report["status"] == "FAIL"]

    assert (
        failed["record_count_csv"]
        != failed["record_count_db"]
    ).any()
