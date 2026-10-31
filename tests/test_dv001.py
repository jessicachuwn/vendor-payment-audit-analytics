

import pandas as pd


def test_reconciliation_detects_difference():
    csv_summary = pd.DataFrame({
        "legal_entity": ["US01"],
        "currency": ["USD"],
        "record_count": [2],
        "total_amount_cents": [100000],
    })

    db_summary = pd.DataFrame({
        "legal_entity": ["US01"],
        "currency": ["USD"],
        "record_count": [2],
        "total_amount_cents": [90000],
    })

    result = csv_summary.merge(
        db_summary,
        on=["legal_entity", "currency"],
        suffixes=("_csv", "_db"),
    )

    passed = (
        result["record_count_csv"].eq(
            result["record_count_db"]
        )
        & result["total_amount_cents_csv"].eq(
            result["total_amount_cents_db"]
        )
    )

    assert not passed.all()
