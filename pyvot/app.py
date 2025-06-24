from io import StringIO
from fasthtml.common import *
from pathlib import Path
import pandas as pd

app, rt = fast_app(
    debug=True,
    title="Pyvot",
    hdrs=[
        Script(
            src="https://cdn.jsdelivr.net/npm/@alpinejs/sort@3.x.x/dist/cdn.min.js",
            defer=True,
        ),
        Script(
            src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js",
            defer=True,
        ),
    ],
)

UPLOAD_DIR = Path("datasets")
UPLOAD_DIR.mkdir(exist_ok=True)


def upload_page(errors: list[str] = []):
    return Titled(
        "Pyvot",
        Article(
            Form(method="post", action=upload)(
                Input(type="file", name="file"),
                Button("Upload", type="submit", cls="secondary"),
                Div(cls="errors")(*[Div(error, cls="error") for error in errors]),
            ),
            Div(cls="info")(
                "Upload a CSV file to generate a pivot table.",
                "After uploading, you can select rows, columns, and aggregation functions.",
            ),
        ),
    )


def checkbox_select(options: list[str], name: str = ""):
    return [
        Label(
            opt,
            Input(
                id=f'{opt.replace(" ", "")}',
                name=name,
                value=opt,
                type="checkbox",
                checked=True,
                hidden=True,
            ),
            **{"x-sort:item": f'{opt.replace(" ", "")}'},
            style='''
                background-color: var(--pico-primary-background);
                padding: 5px 10px; margin: 5px;
                border: 1px solid var(--pico-primary-border);
                border-radius: 4px; display: inline-block;
            ''',
        )
        for opt in options
    ]

def agg_select(agg: str):
    return Select(
        "Aggregation",
        *[
            Option(f, value=f, selected=(f == agg))
            for f in ("count", "sum", "mean", "min", "max")
        ],
        name="agg",
        cls="select",
    ),

def pivot_form(
    columns: list[str], row: list[str], col: list[str], val: list[str], agg: str
):
    unused_columns = set(columns) - set(row) - set(col) - set(val)
    return Div(
        Div(
            *checkbox_select(unused_columns),
            ** {"x-sort": f'(item) => sort(item, "")', "x-sort:group": "pivot"},
        ),
        Form(
            Div(
                "Rows",
                *checkbox_select(row, name="row"),
                style="border: 1px solid #ccc; padding: 2rem;",
                **{"x-sort": '(item) => sort(item, "row")', "x-sort:group": "pivot"},
            ),
            Div(
                "Columns",
                *checkbox_select(col, name="col"),
                style="border: 1px solid #ccc; padding: 2rem;",
                **{"x-sort": '(item) => sort(item, "col")', "x-sort:group": "pivot"},
            ),
            Div(
                "Values",
                *checkbox_select(val, name="val"),
                style="border: 1px solid #ccc; padding: 2rem;",
                **{"x-sort": '(item) => sort(item, "val")', "x-sort:group": "pivot"},
            ),
            Label(
                "Aggregation",
                agg_select(agg),
            ),
            Button("Generate Pivot", type="submit", cls="secondary"),
            method="get",
            action=".",
        ),
        **{
            "x-data": """{
            sort(item, select) { item.name = select }
        }"""
        },
    )


def clean(df: pd.DataFrame):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # strip whitespaces from all cells
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df


def process_csv(csv: str):
    try:
        df = pd.read_csv(csv)
        df = clean(df)
        return df
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
    file_path = UPLOAD_DIR / f"{filename}.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found.")
    df = pd.read_csv(file_path)
    columns = df.columns.tolist()
    if row or col:
        df = pd.pivot_table(df, values=val, index=row, columns=col, aggfunc=agg)
    return Titled(
        f"{filename.title()}",
        Article(
            Div(pivot_form(columns, row=row, col=col, val=val, agg=agg), id="pivot"),
            Div(
                NotStr(
                    df.to_html(),
                ),
                id="data",
                style="overflow-x:auto;",
            ),
        ),
    )


@app.get("/")
async def home(
    filename: str = "",
    val: list[str] = [],
    row: list[str] = [],
    col: list[str] = [],
    agg: str = "count",
):
    return upload_page()


@app.post("/")
async def upload(file: UploadFile):
    filebuffer = await file.read()
    if not file.filename.endswith(".csv"):
        return upload_page(errors=["Only .csv files allowed."])
    if (UPLOAD_DIR / file.filename).exists():
        return upload_page(errors=[f"File already exists."])
    try:
        csv_str = StringIO(filebuffer.decode("utf-8"))
        df = process_csv(csv_str)
    except HTTPException as e:
        return upload_page(errors=[e.detail])
    df.to_csv(UPLOAD_DIR / file.filename, index=False)
    return Redirect(f"/{file.filename.replace('.csv', '')}/")


serve()
