"""Read a source CSV exactly as received: every value stays text."""
import re
from pathlib import Path

import pandas as pd


def clean_column_name(name):
    """'Area Code (M49)' -> 'area_code_m49'"""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def read_raw_csv(path, encoding="utf-8"):
    path = Path(path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding=encoding)
    df.columns = [clean_column_name(c) for c in df.columns]
    df["_source_file"] = path.name
    return df