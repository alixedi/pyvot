from io import StringIO
from fasthtml.common import *
from pathlib import Path
import pandas as pd

app, rt = fast_app(
    debug=True,
    title="Pyvot",
    hdrs=[
        Script(
            src='https://cdn.jsdelivr.net/npm/@alpinejs/sort@3.x.x/dist/cdn.min.js',
            defer=True,
        ),
        Script(
            src='https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js',
            defer=True,
        ),
    ],
)

UPLOAD_DIR = Path("datasets")
UPLOAD_DIR.mkdir(exist_ok=True)

def upload_page(errors: list[str] = []):
    return Titled("Pyvot",
            Article(
                Form(method='post', action=upload)(
                    Input(type="file", name="file"),
                    Button("Upload", type="submit", cls='secondary'),
                    Div(cls='errors')(
                        *[Div(error, cls='error') for error in errors]
                    ),
                ),
                Div(cls='info')(
                    "Upload a CSV file to generate a pivot table.",
                    "After uploading, you can select rows, columns, and aggregation functions."
                )
            ),
        )

def pivot_form(columns: list[str], row: list[str], col: list[str], val: list[str], agg: str):
    return Form(
        Label(
            'Rows',
            Select(
                "Rows",
                *[Option(c, value=c, selected=(c in row)) for c in columns],
                name='row',
                multiple=True,
                cls='select',
            ),
        ),
        Label(
            'Columns',
            Select(
                "Columns",
                *[Option(c, value=c, selected=(c in col)) for c in columns],
                name='col',
                multiple=True,
                cls='select',
            ),
        ),
        Label(
            'Values',
            Select(
                "Values",
                *[Option(c, value=c, selected=(c in val)) for c in columns],
                name='val',
                multiple=True,
                cls='select',
            ),
        ),
        Label(
            'Aggregation',
            Select(
                "Aggregation",
                *[Option(f, value=f, selected=(f == agg)) for f in ('count', 'sum', 'mean', 'min', 'max')],
                name='agg',
                multiple=True,
                cls='select',
            ),
        ),
        Button("Generate Pivot", type="submit", cls='secondary'),
        method='get',
        action='.',
    )

def clean(df: pd.DataFrame):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    return df

def process_csv(csv: str):
    try:
        df = pd.read_csv(csv)
        df = clean(df)
        return df
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail=f"File is empty."
        )
    except pd.errors.ParserError:
        raise HTTPException(
            status_code=400,
            detail=f"File is not valid CSV."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error while processing file.: {str(e)}"
        )

@app.get('/{filename}')
async def home(filename: str='', val: list[str]=[], row: list[str]=[], col: list[str]=[], agg: str='count'):
    if not filename:
        return upload_page()
    file_path = UPLOAD_DIR / f'{filename}.csv'
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found.")
    df = pd.read_csv(file_path)
    columns = df.columns.tolist()
    if (row or col):
        df = pd.pivot_table(df, values=val, index=row, columns=col, aggfunc=agg)
    return Titled(f"{filename}",
        Article(
            *[Button(col) for col in columns],
            Div(NotStr(df.to_html(), ), id='data'),
            Div(pivot_form(columns, row, col, val, agg), id='pivot')
        ),
    )

@app.post('/')
async def upload(file: UploadFile):
    filebuffer = await file.read()
    if not file.filename.endswith('.csv'):
        return upload_page(errors=["Only .csv files allowed."])
    if (UPLOAD_DIR / file.filename).exists():
        return upload_page(errors=[f"File already exists."])
    try:
        csv_str = StringIO(filebuffer.decode('utf-8'))
        df = process_csv(csv_str)
    except HTTPException as e:
        return upload_page(errors=[e.detail])
    df.to_csv(UPLOAD_DIR / file.filename, index=False)
    return Redirect(f"/{file.filename.replace('.csv', '')}")

serve()
