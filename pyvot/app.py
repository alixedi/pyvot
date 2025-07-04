from io import StringIO
from pathlib import Path

from fasthtml.common import *
import pandas as pd

from pyvot.csv import clean, typer
from pyvot.forms import pivot_form, upload_form


SECRET_URL = 'e7kqnVDdGOQNMa6C'
UPLOAD_DIR = Path("datasets")
UPLOAD_DIR.mkdir(exist_ok=True)
ALPINE_CDN = 'https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js'
ALPINE_SORT_CDN = 'https://cdn.jsdelivr.net/npm/@alpinejs/sort@3.x.x/dist/cdn.min.js'


app, rt = fast_app(
    debug=True,
    title="Pyvot",
    hdrs=[
        Script(src=ALPINE_SORT_CDN, defer=True),
        Script(src=ALPINE_CDN, defer=True),
    ],
)


def upload_page(errors: list[str] = []):
    return Titled("Pyvot", Article(upload_form(upload, errors)))


def process_csv(csv: str):
    try:
        df = pd.read_csv(csv, skipinitialspace=True, thousands=',')
        dfc = clean(df)
        dft = typer(dfc)
        return dft
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail=f"File is empty.")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail=f"File is not valid CSV.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while processing file.: {str(e)}"
        )


@app.get("/{filename}/")
async def pivot(
    filename: str = "",
    row: list[str] = [],
    col: list[str] = [],
    val: list[str] = [],
    agg: str = "count",
):
    if not filename:
        return upload_page()
    file_path = UPLOAD_DIR / f"{filename}.parquet"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found.")
    df = pd.read_parquet(file_path)
    columns = df.columns.tolist()
    if row or col:
        df = pd.pivot_table(df, values=val, index=row, columns=col, aggfunc=agg, fill_value=0)
    st = df.style.background_gradient(cmap='YlGnBu')
    return Titled(
        f"{filename.title()}",
        Article(
            Div(pivot_form(columns, row=row, col=col, val=val, agg=agg), id="pivot"),
            Div(
                NotStr(st.to_html(na_rep="")),
                id="data",
                style="overflow-x:auto;",
            ),
        ),
    )


@app.get(f"/{SECRET_URL}")
async def home(
    filename: str = "",
    val: list[str] = [],
    row: list[str] = [],
    col: list[str] = [],
    agg: str = "count",
):
    return upload_page()


@app.post(f"/{SECRET_URL}")
async def upload(file: UploadFile):
    filebuffer = await file.read()
    stem = Path(file.filename).stem
    filename = f"{stem}.parquet"
    if not file.filename.endswith(".csv"):
        return upload_page(errors=["Only .csv files allowed."])
    if (UPLOAD_DIR / filename).exists():
        return upload_page(errors=[f"File already exists."])
    try:
        csv_str = StringIO(filebuffer.decode("utf-8", errors='ignore'))
        df = process_csv(csv_str)
    except HTTPException as e:
        return upload_page(errors=[e.detail])
    df.to_parquet(UPLOAD_DIR / f'{stem}.parquet', index=False)
    return Redirect(f"/{stem}/")
