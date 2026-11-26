"""Helper for validation checks.

Rows that fail a check are set aside and recorded, never silently dropped.
"""
import json

import pandas as pd


class Checker:
    def __init__(self, dataset):
        self.dataset = dataset
        self.results = []    # one dict per check, for quality_log
        self.rejected = []   # DataFrames of failed rows, for rejected_rows

    def info(self, check_name, rows_checked, rows_excluded):
        """Record a step that removes rows on purpose (not a failure)."""
        self.results.append({
            "check_name": check_name,
            "rows_checked": int(rows_checked),
            "rows_failed": int(rows_excluded),
            "status": "info",
        })

    def run(self, df, check_name, bad_mask, reason):
        """Set aside the rows where bad_mask is True; return the rows that passed."""
        bad_mask = bad_mask.astype(bool)
        bad = df[bad_mask]
        self.results.append({
            "check_name": check_name,
            "rows_checked": len(df),
            "rows_failed": len(bad),
            "status": "pass" if bad.empty else "fail",
        })
        if not bad.empty:
            self.rejected.append(bad.assign(_check_name=check_name, _reason=reason))
        return df[~bad_mask]

    def rejected_records(self):
        """Failed rows as plain dicts, ready to insert into rejected_rows."""
        records = []
        for frame in self.rejected:
            for _, row in frame.iterrows():
                data = {k: str(v) for k, v in row.items()
                        if k not in ("_check_name", "_reason")}
                records.append({
                    "check_name": row["_check_name"],
                    "reason": row["_reason"],
                    "row_data": json.dumps(data),
                })
        return records

    def summary_lines(self):
        return [
            f"  {r['check_name']:<22} checked {r['rows_checked']:>6}  "
            f"failed {r['rows_failed']:>5}  {r['status']}"
            for r in self.results
        ]