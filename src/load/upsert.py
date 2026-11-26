"""Generic upsert: insert new rows, update changed rows, leave identical rows alone."""
from sqlalchemy import text


def upsert(conn, df, table, key_cols, schema="staging"):
    """Merge a DataFrame into schema.table. Returns counts of what happened."""
    if df.empty:
        return {"inserted": 0, "updated": 0, "unchanged": 0}

    cols = list(df.columns)
    value_cols = [c for c in cols if c not in key_cols]
    target = f"{schema}.{table}"
    incoming = f"incoming_{table}"   # one temp table per target, so calls never clash

    # 1. Park the incoming rows in a temporary table that vanishes at commit
    conn.execute(text(
        f"CREATE TEMP TABLE {incoming} (LIKE {target} INCLUDING DEFAULTS) ON COMMIT DROP"
    ))
    df.to_sql(incoming, conn, if_exists="append", index=False,
              method="multi", chunksize=1000)

    # 2. Merge. A conflict on the key means the row already exists.
    #    It is only updated if some value actually differs.
    old_values = ", ".join(f"{target}.{c}" for c in value_cols)
    new_values = ", ".join(f"EXCLUDED.{c}" for c in value_cols)
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in value_cols)
    sql = f"""
        INSERT INTO {target} ({", ".join(cols)})
        SELECT {", ".join(cols)} FROM {incoming}
        ON CONFLICT ({", ".join(key_cols)}) DO UPDATE
        SET {updates}, _updated_at = now()
        WHERE ({old_values}) IS DISTINCT FROM ({new_values})
        RETURNING (xmax = 0) AS inserted
    """
    rows = conn.execute(text(sql)).fetchall()

    # RETURNING only lists rows that were inserted or updated.
    # xmax = 0 marks a brand-new row; anything else was an update.
    inserted = sum(1 for r in rows if r.inserted)
    updated = len(rows) - inserted
    return {"inserted": inserted, "updated": updated, "unchanged": len(df) - len(rows)}