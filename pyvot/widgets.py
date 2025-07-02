from fasthtml.common import *


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
    )


def drop_div(name: str, data=list[str]):
    return Label(
        f"{name.title()}s",
        Div(
            *checkbox_select(data, name=name),
            style='''
                border: 1px solid var(--pico-h1-color); border-radius: 4px;
                padding: 0.5rem; min-height: 4em;
            ''',
            **{"x-sort": f'(item) => sort(item, "{name}")', "x-sort:group": "pivot"},
        ),
        style="width: 100%;"
    )
