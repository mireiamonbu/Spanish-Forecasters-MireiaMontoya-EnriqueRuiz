import numpy as np
import pandas as pd
from pathlib import Path

CHUNKS_DIR = Path("project/data/CSVs")
OUT_PATH   = Path("project/data/processed/ree_panel_top7.parquet")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

TOP_K = 7  # keep only Top-7 technologies by mean daily generation


def parse_ree_csv_wide_to_long(path: Path) -> pd.DataFrame:
    # REE CSV is wide: rows=technologies, columns=dates
    raw = pd.read_csv(path, header=None, encoding="latin1")

    # find the row that starts the date header ("Fecha")
    r = raw.index[raw.iloc[:, 0].astype(str).str.strip().eq("Fecha")]
    if len(r) == 0:
        raise ValueError(f"'Fecha' row not found in {path}")
    r = r[0]

    # parse date columns (either dd/mm/YYYY or ISO-like)
    dates = []
    for d in raw.iloc[r, 1:].tolist():
        s = str(d).strip()
        if "/" in s:
            dates.append(pd.to_datetime(s.split()[0], format="%d/%m/%Y", errors="coerce"))
        else:
            dates.append(pd.to_datetime(s[:10], errors="coerce"))  # YYYY-MM-DD

    # take the block below the header
    block = raw.iloc[r + 1:].dropna(how="all")
    block = block[block.iloc[:, 0].notna()].copy()
    block.columns = ["unique_id"] + dates

    # long format: unique_id, ds, y
    df = block.melt(id_vars="unique_id", var_name="ds", value_name="y")
    df["unique_id"] = df["unique_id"].astype(str).str.strip()
    df["ds"] = pd.to_datetime(df["ds"], errors="coerce").dt.normalize()

    # parse numbers: comma decimals, "-" as missing
    y = (df["y"].astype(str).str.strip()
         .replace({"-": np.nan, "": np.nan})
         .str.replace(".", "", regex=False)
         .str.replace(",", ".", regex=False))
    df["y"] = pd.to_numeric(y, errors="coerce").clip(lower=0)

    df = df.dropna(subset=["unique_id", "ds", "y"])
    df = df[df["unique_id"].ne("")]
    return df[["unique_id", "ds", "y"]]


# 1) read all yearly CSVs and combine
files = sorted(CHUNKS_DIR.glob("ree_gen_day_*.csv"))
if not files:
    raise FileNotFoundError(f"No CSV files found in: {CHUNKS_DIR.resolve()}")

df = pd.concat([parse_ree_csv_wide_to_long(f) for f in files], ignore_index=True)

# 2) clean
df = df.drop_duplicates(["unique_id", "ds"]).sort_values(["unique_id", "ds"])
df = df[df["unique_id"] != "Generación total"].copy()

# 3) keep only Top-K technologies by mean generation
top_ids = df.groupby("unique_id")["y"].mean().sort_values(ascending=False).head(TOP_K).index
df = df[df["unique_id"].isin(top_ids)].copy()

# 4) create full daily grid and fill missing values
all_dates = pd.date_range(df["ds"].min(), df["ds"].max(), freq="D")
uids = df["unique_id"].unique()

full = pd.MultiIndex.from_product([uids, all_dates], names=["unique_id", "ds"]).to_frame(index=False)
df = full.merge(df, on=["unique_id", "ds"], how="left").sort_values(["unique_id", "ds"])

# safe filling for forecasting: forward-fill only, then 0 at the beginning if needed
df["y"] = df.groupby("unique_id")["y"].ffill().fillna(0.0)

# 5) save
df.to_parquet(OUT_PATH, index=False)
print(f"Saved: {OUT_PATH} | shape={df.shape} | series={df['unique_id'].nunique()}")
