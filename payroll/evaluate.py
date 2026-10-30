def summarize(connection, ground_truth=None):
    tables = ["pay_group", "employee", "pay_period", "time_entry", "leave_record", "allowance", "deduction", "payroll_input", "validation_rule", "exception_record", "approval", "payroll_export"]
    metrics = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
    metrics["source_transactions"] = metrics["time_entry"] + metrics["allowance"] + metrics["deduction"]
    metrics["open_exceptions"] = connection.execute("SELECT COUNT(*) FROM exception_record WHERE status='OPEN'").fetchone()[0]
    metrics["fk_violations"] = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    metrics["exports_with_open_exceptions"] = connection.execute(
        "SELECT COUNT(*) FROM payroll_export x JOIN exception_record e "
        "ON x.employee_id=e.employee_id AND x.pay_period_id=e.pay_period_id WHERE e.status='OPEN'"
    ).fetchone()[0]
    metrics["export_duplicates"] = connection.execute("SELECT COUNT(*)-COUNT(DISTINCT payroll_input_id) FROM payroll_export").fetchone()[0]
    metrics["missing_approval"] = connection.execute(
        "SELECT COUNT(*) FROM payroll_export x LEFT JOIN approval a ON a.approval_id=x.approval_id "
        "WHERE a.approval_id IS NULL OR a.decision<>'APPROVED'"
    ).fetchone()[0]
    if ground_truth is not None:
        expected = {(code, record_id) for code, ids in ground_truth.items() for record_id in ids}
        actual = {(r["rule_code"], r["record_id"]) for r in connection.execute(
            "SELECT v.rule_code,e.record_id FROM exception_record e JOIN validation_rule v ON v.rule_id=e.rule_id"
        )}
        tp, fp, fn = len(expected & actual), len(actual - expected), len(expected - actual)
        metrics["detection"] = {"true_positive": tp, "false_positive": fp, "false_negative": fn,
                                 "precision": round(tp / (tp + fp), 4) if tp + fp else 1.0,
                                 "recall": round(tp / (tp + fn), 4) if tp + fn else 1.0}
    return metrics
