from collections.abc import Callable
from fasthtml.common import *
from pyvot.widgets import *


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
            drop_div("row", row),
            drop_div("col", col),
            drop_div("val", val),
            Label("Aggregation", agg_select(agg)),
            Button("Generate Pivot", type="submit", cls="secondary"),
            method="get",
            action=".",
            style="display: flex; flex-direction: column; gap: 1em; margin: 1em 0em;"
        ),
        **{"x-data": """{sort(item, select) { item.name = select }}"""},
    )


def upload_form(action: Callable, errors: list[str] = []):
    return Div(
        Form(method="post", action=action)(
            Input(type="file", name="file"),
            Button("Upload", type="submit", cls="secondary"),
            Div(cls="errors")(*[Div(error, cls="error") for error in errors]),
        ),
        Div(cls="info")(
            "Upload a CSV file to generate a pivot table.",
            "After uploading, you can select rows, columns, and aggregation functions.",
        ),
    )
