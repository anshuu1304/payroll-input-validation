import os
import tempfile
import pytest
from payroll.db import connect, initialize
from payroll.generate import seed_data
from payroll.workflow import build_payroll, process
from payroll.evaluate import summarize


@pytest.fixture
def payroll_db():
    handle = tempfile.NamedTemporaryFile(delete=False)
    handle.close()
    connection = connect(handle.name)
    initialize(connection)
    generated = seed_data(connection, 100)
    truth = generated.pop("ground_truth")
    build_payroll(connection)
    process(connection)
    yield connection, truth
    connection.close()
    os.unlink(handle.name)


def test_all_twelve_entities_and_foreign_keys(payroll_db):
    connection, _ = payroll_db
    expected = {"pay_group", "employee", "pay_period", "time_entry", "leave_record", "allowance", "deduction", "payroll_input", "validation_rule", "exception_record", "approval", "payroll_export"}
    actual = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert expected <= actual
    assert not connection.execute("PRAGMA foreign_key_check").fetchall()


def test_five_rules_are_independently_detected(payroll_db):
    connection, truth = payroll_db
    metrics = summarize(connection, truth)["detection"]
    assert metrics == {"true_positive": 52, "false_positive": 0, "false_negative": 0, "precision": 1.0, "recall": 1.0}


def test_clean_baseline_has_no_duplicate_allowance_findings():
    handle = tempfile.NamedTemporaryFile(delete=False)
    handle.close()
    connection = connect(handle.name)
    initialize(connection)
    seed_data(connection, 25, inject_anomalies=False)
    from payroll.validate import detect
    assert not [item for item in detect(connection) if item[0] in {"R02", "R04"}]
    connection.close()
    os.unlink(handle.name)


def test_open_exceptions_block_export(payroll_db):
    connection, _ = payroll_db
    metrics = summarize(connection)
    assert metrics["exports_with_open_exceptions"] == 0
    assert metrics["missing_approval"] == 0


def test_reprocessing_does_not_duplicate_exports(payroll_db):
    connection, _ = payroll_db
    before = connection.execute("SELECT COUNT(*) FROM payroll_export").fetchone()[0]
    process(connection)
    after = connection.execute("SELECT COUNT(*) FROM payroll_export").fetchone()[0]
    assert after == before


def test_unique_payroll_input_per_employee_period(payroll_db):
    connection, _ = payroll_db
    row = connection.execute("SELECT employee_id,pay_period_id FROM payroll_input LIMIT 1").fetchone()
    with pytest.raises(Exception):
        connection.execute("INSERT INTO payroll_input VALUES('duplicate',?,?,0,0,0,'PENDING')", tuple(row))


def test_full_volume_generation_exceeds_100k():
    handle = tempfile.NamedTemporaryFile(delete=False)
    handle.close()
    connection = connect(handle.name)
    initialize(connection)
    generated = seed_data(connection, 3000)
    assert generated["time"] + generated["allowance"] + generated["deduction"] >= 100000
    assert not connection.execute("PRAGMA foreign_key_check").fetchall()
    connection.close()
    os.unlink(handle.name)


def test_reconciliation_detects_independent_total_tampering():
    handle = tempfile.NamedTemporaryFile(delete=False)
    handle.close()
    connection = connect(handle.name)
    initialize(connection)
    seed_data(connection, 3, inject_anomalies=False)
    build_payroll(connection)
    connection.execute("UPDATE payroll_input SET net_pay=net_pay+1 WHERE employee_id='EMP000001' AND pay_period_id='PP1'")
    from payroll.validate import detect
    findings = [item for item in detect(connection) if item[0] == "R05"]
    assert len(findings) == 1 and findings[0][1:3] == ("EMP000001", "PP1")
    connection.close()
    os.unlink(handle.name)


def test_reprocessing_does_not_duplicate_audit_events(payroll_db):
    connection, _ = payroll_db
    before = connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    process(connection)
    after = connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert after == before


def test_unapproved_time_period_is_not_exported(payroll_db):
    connection, _ = payroll_db
    rows = connection.execute(
        "SELECT DISTINCT t.employee_id,t.pay_period_id FROM time_entry t "
        "WHERE t.approved=0"
    ).fetchall()
    for employee_id, period_id in rows:
        assert connection.execute(
            "SELECT 1 FROM payroll_export WHERE employee_id=? AND pay_period_id=?",
            (employee_id, period_id),
        ).fetchone() is None
