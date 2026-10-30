import argparse
import json
import os
from pathlib import Path
from .db import connect, initialize
from .generate import seed_data
from .workflow import build_payroll, process
from .evaluate import summarize


def main():
    parser = argparse.ArgumentParser(description="Synthetic payroll validation and reconciliation demo")
    parser.add_argument("--size", choices=["small", "full"], default="small")
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--db", default="payroll.db")
    args = parser.parse_args()
    if os.path.exists(args.db):
        os.remove(args.db)
    connection = connect(args.db)
    try:
        initialize(connection)
        generated = seed_data(connection, 100 if args.size == "small" else 3000, args.seed)
        ground_truth = generated.pop("ground_truth")
        build_payroll(connection)
        process(connection)
        report = {"seed": args.seed, "size": args.size, "generated": generated,
                  "metrics": summarize(connection, ground_truth)}
        output = Path("reports")
        output.mkdir(exist_ok=True)
        (output / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2))
        (output / "summary.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
