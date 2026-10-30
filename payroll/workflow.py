from datetime import datetime, timezone


def stamp():
    return datetime.now(timezone.utc).isoformat()


def expected_totals(connection):
    """Recompute payroll totals from raw source tables, independent of payroll_input."""
    rows = connection.execute(
        "WITH t AS (SELECT employee_id,pay_period_id,SUM(CASE WHEN approved=1 THEN hours ELSE 0 END) hours FROM time_entry GROUP BY employee_id,pay_period_id), "
        "a AS (SELECT employee_id,pay_period_id,SUM(amount) amount FROM allowance GROUP BY employee_id,pay_period_id), "
        "d AS (SELECT employee_id,pay_period_id,SUM(amount) amount FROM deduction GROUP BY employee_id,pay_period_id) "
        "SELECT e.employee_id,p.pay_period_id,ROUND(COALESCE(t.hours,0)*e.hourly_rate+COALESCE(a.amount,0),2) gross, "
        "ROUND(COALESCE(d.amount,0),2) deductions "
        "FROM employee e CROSS JOIN pay_period p "
        "LEFT JOIN t ON t.employee_id=e.employee_id AND t.pay_period_id=p.pay_period_id "
        "LEFT JOIN a ON a.employee_id=e.employee_id AND a.pay_period_id=p.pay_period_id "
        "LEFT JOIN d ON d.employee_id=e.employee_id AND d.pay_period_id=p.pay_period_id"
    )
    return {(r["employee_id"], r["pay_period_id"]): (r["gross"], r["deductions"], round(r["gross"] - r["deductions"], 2)) for r in rows}


def build_payroll(connection):
    totals = expected_totals(connection)
    rows = [
        (f"PI-{employee_id}-{period_id}", employee_id, period_id, gross, deductions, net, "PENDING")
        for (employee_id, period_id), (gross, deductions, net) in totals.items()
    ]
    connection.executemany("INSERT INTO payroll_input VALUES(?,?,?,?,?,?,?)", rows)

    # Controlled data-integrity defects simulate a corrupted upstream payroll feed.
    for employee_no in range(22, 27):
        employee_id = f"EMP{employee_no:06}"
        connection.execute(
            "UPDATE payroll_input SET gross_pay=gross_pay+125.00 WHERE employee_id=? AND pay_period_id='PP1'",
            (employee_id,),
        )
    connection.commit()


def process(connection):
    from .validate import detect
    findings = detect(connection)
    connection.executemany(
        "INSERT OR IGNORE INTO exception_record VALUES(?,?,?,?,?,?,?)",
        [(f"EX-{record_id}", f"RULE-{code}", employee_id, period_id, record_id, message, "OPEN")
         for code, employee_id, period_id, record_id, message in findings],
    )
    connection.commit()

    # Only inputs with no open blocking exception may be approved or exported.
    eligible = connection.execute(
        "SELECT p.* FROM payroll_input p WHERE NOT EXISTS (SELECT 1 FROM exception_record e "
        "WHERE e.employee_id=p.employee_id AND e.pay_period_id=p.pay_period_id AND e.status='OPEN')"
    ).fetchall()
    now = stamp()
    for row in eligible:
        approval_id = f"AP-{row['payroll_input_id']}"
        connection.execute(
            "INSERT OR IGNORE INTO approval VALUES(?,?,?,?,?)",
            (approval_id, row["payroll_input_id"], "PAYROLL_MANAGER", "APPROVED", now),
        )
        connection.execute("UPDATE payroll_input SET status='APPROVED' WHERE payroll_input_id=?", (row["payroll_input_id"],))
        exported = connection.execute(
            "INSERT OR IGNORE INTO payroll_export VALUES(?,?,?,?,?,?,?)",
            (f"EXP-{row['payroll_input_id']}", row["payroll_input_id"], approval_id, row["employee_id"], row["pay_period_id"], row["net_pay"], now),
        )
        if exported.rowcount:
            connection.execute(
                "INSERT INTO audit_log(entity_type,entity_id,action,new_value,actor,event_at) VALUES(?,?,?,?,?,?)",
                ("PayrollInput", row["payroll_input_id"], "APPROVED_AND_EXPORTED", "APPROVED", "PAYROLL_MANAGER", now),
            )
    connection.commit()
