import dateutil
import pandas as pd


def typer(df):
    df2 = df.copy()
    for col in df2.columns:
        # Is it a number?
        try:
            df2[col] = pd.to_numeric(df[col])
            continue
        except Exception:
            pass
        # Is it a date?
        try:
            df2[col] = df[col].apply(dateutil.parser.parse)
            df2[col] = pd.to_datetime(df2[col])
            continue
        except Exception as e:
            pass
    return df2


def clean(df: pd.DataFrame):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # strip whitespaces from all cells
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Remove non-space and non-alphanumerics
    df.columns = df.columns.str.replace(r'[^A-Za-z0-9 ]+', '', regex=True)
    return df
