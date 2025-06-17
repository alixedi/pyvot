from io import StringIO
from fasthtml.common import *
from pathlib import Path
import pandas as pd

app, rt = fast_app(debug=True, title="Pyvot")

UPLOAD_DIR = Path("datasets")
UPLOAD_DIR.mkdir(exist_ok=True)

def upload_form(errors: list[str] = []):
    return Titled(
        "File Upload Demo",
        Article(
            Form(method='post', action=upload)(
                Input(type="file", name="file"),
                Button("Upload", type="submit", cls='secondary'),
                Div(cls='errors')(
                    *[Div(error, cls='error') for error in errors]
                ),
            ),
        ),
    )

def clean_data(df: pd.DataFrame):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    return df

def check_csv(csv: str):
    try:
        df = pd.read_csv(csv)
        # Strip whitespace from column names todo: do this on upload
        df.columns=df.columns.str.strip()
        # clean df
        df = clean_data(df)
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
        return upload_form()
    file_path = UPLOAD_DIR / f'{filename}.csv'
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found.")
    df = pd.read_csv(file_path)
    if (row or col):
        df = pd.pivot_table(df, values=val, index=row, columns=col, aggfunc=agg)
    return Titled(f"{filename}",
        Article(
            NotStr(df.to_html(), ),
        )
    )

@app.post('/')
async def upload(file: UploadFile):
    filebuffer = await file.read()
    if not file.filename.endswith('.csv'):
        return upload_form(errors=["Only .csv files allowed."])
    if (UPLOAD_DIR / file.filename).exists():
        return upload_form(errors=[f"File already exists."])
    try:
        csv_str = StringIO(filebuffer.decode('utf-8'))
        check_csv(csv_str)
    except HTTPException as e:
        return upload_form(errors=[e.detail])
    (UPLOAD_DIR / file.filename).write_bytes(filebuffer)
    return Redirect(f"/{file.filename.replace('.csv', '')}")

serve()
