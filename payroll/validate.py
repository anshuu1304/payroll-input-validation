def detect(connection):
    findings = []
    for row in connection.execute("SELECT time_entry_id,employee_id,pay_period_id,hours FROM time_entry WHERE hours>80"):
        findings.append(("R01", row["employee_id"], row["pay_period_id"], row["time_entry_id"], "Hours exceed the 80-hour validation threshold"))
    for row in connection.execute(
        "SELECT a.employee_id,a.pay_period_id,a.allowance_id FROM allowance a "
        "JOIN (SELECT employee_id,pay_period_id,allowance_type,MIN(allowance_id) keep_id "
        "FROM allowance GROUP BY employee_id,pay_period_id,allowance_type HAVING COUNT(*)>1) d "
        "ON a.employee_id=d.employee_id AND a.pay_period_id=d.pay_period_id "
        "AND a.allowance_type=d.allowance_type WHERE a.allowance_id<>d.keep_id"
    ):
        findings.append(("R02", row["employee_id"], row["pay_period_id"], row["allowance_id"], "Duplicate allowance type in employee pay period"))
    for row in connection.execute("SELECT time_entry_id,employee_id,pay_period_id FROM time_entry WHERE approved=0"):
        findings.append(("R03", row["employee_id"], row["pay_period_id"], row["time_entry_id"], "Unapproved time entry included in payroll source"))
    for row in connection.execute(
        "SELECT d.deduction_id,d.employee_id,d.pay_period_id FROM deduction d "
        "JOIN (SELECT employee_id,pay_period_id,leave_record_id,deduction_type,MIN(deduction_id) keep_id "
        "FROM deduction WHERE deduction_type='LEAVE' AND leave_record_id IS NOT NULL "
        "GROUP BY employee_id,pay_period_id,leave_record_id,deduction_type HAVING COUNT(*)>1) x "
        "ON d.employee_id=x.employee_id AND d.pay_period_id=x.pay_period_id "
        "AND d.leave_record_id=x.leave_record_id AND d.deduction_type=x.deduction_type "
        "WHERE d.deduction_id<>x.keep_id"
    ):
        findings.append(("R04", row["employee_id"], row["pay_period_id"], row["deduction_id"], "Duplicate leave deduction for the same leave record"))

    # Deliberately independent aggregation path: do not reuse the payroll builder's CTE/function.
    hours_by_period = {(r["employee_id"], r["pay_period_id"]): r["hours"] for r in connection.execute(
        "SELECT employee_id,pay_period_id,SUM(CASE WHEN approved=1 THEN hours ELSE 0 END) hours "
        "FROM time_entry GROUP BY employee_id,pay_period_id")}
    allowance_by_period = {(r["employee_id"], r["pay_period_id"]): r["amount"] for r in connection.execute(
        "SELECT employee_id,pay_period_id,SUM(amount) amount FROM allowance GROUP BY employee_id,pay_period_id")}
    deduction_by_period = {(r["employee_id"], r["pay_period_id"]): r["amount"] for r in connection.execute(
        "SELECT employee_id,pay_period_id,SUM(amount) amount FROM deduction GROUP BY employee_id,pay_period_id")}
    rates = {r["employee_id"]: r["hourly_rate"] for r in connection.execute("SELECT employee_id,hourly_rate FROM employee")}
    for row in connection.execute("SELECT * FROM payroll_input"):
        key = (row["employee_id"], row["pay_period_id"])
        gross_raw = hours_by_period.get(key, 0.0) * rates[row["employee_id"]] + allowance_by_period.get(key, 0.0)
        gross, deductions = connection.execute(
            "SELECT ROUND(?,2),ROUND(?,2)", (gross_raw, deduction_by_period.get(key, 0.0))
        ).fetchone()
        net = connection.execute("SELECT ROUND(?-?,2)", (gross, deductions)).fetchone()[0]
        if any(abs(actual - target) > 0.01 for actual, target in ((row["gross_pay"], gross), (row["deductions"], deductions), (row["net_pay"], net))):
            findings.append(("R05", row["employee_id"], row["pay_period_id"], row["payroll_input_id"], "Stored payroll totals differ from independently aggregated source totals"))
    return findings
