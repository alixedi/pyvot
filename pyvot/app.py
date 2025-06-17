from starlette import status
from fasthtml.common import *
from pathlib import Path
import pandas as pd

app, rt = fast_app(debug=True, title="Pyvot")

UPLOAD_DIR = Path("datasets")
UPLOAD_DIR.mkdir(exist_ok=True)

def upload_form():
    return Form(hx_post=upload, hx_target='#result')(
        Input(type="file", name="file"),
        Button("Upload", type="submit", cls='secondary'),
    )

@app.get('/{filename}')
async def home(filename: str='', val: list[str]=[], row: list[str]=[], col: list[str]=[], agg: str='count'):
    if not filename:
        return Titled("File Upload Demo",
            Article(upload_form()),
            Div(id='result', cls='result'),
        )
    else:
        file_path = UPLOAD_DIR / f'{filename}.csv'
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {filename} not found.")
        try:
            df = pd.read_csv(file_path)
            # Strip whitespace from column names
            df.columns=df.columns.str.strip()
            if (row or col):
                df = pd.pivot_table(df, values=val, index=row, columns=col, aggfunc=agg)
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail=f"File {filename} is empty.")
        except pd.errors.ParserError:
            raise HTTPException(status_code=400, detail=f"File {filename} is not a valid CSV file.")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"An error occurred while processing the file {filename}: {str(e)}")
        return Titled(f"{filename}",
            Article(
                NotStr(df.to_html(), ),
            )
        )

@app.post('/')
async def upload(file: UploadFile):
    filebuffer = await file.read()
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    if (UPLOAD_DIR / file.filename).exists():
        raise HTTPException(status_code=400, detail=f"File {file.filename} already exists.")
    (UPLOAD_DIR / file.filename).write_bytes(filebuffer)
    return Redirect(f"/{file.filename.replace('.csv', '')}")

serve()
