import streamlit as st
import pandas as pd
import ssl
import altair as alt
import datetime
import functools

# Project setup
st.set_page_config(page_title="Scout / Total Dai", page_icon=":coin:", layout="wide")


# SSL setup for local development
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


# Data loader
@st.cache
def load_data(url):
    return pd.read_json(url, typ="frame").data


# Widgets

get_label = lambda c: c["label"]


def make_area_chart(url):
    data = load_data(url)
    st.title(data.title)
    columns = data["columns"]

    cs = functools.reduce(
        (
            lambda acc, col: [acc[0] + ["Date"], acc[1]]
            if col["label"] == ""
            else [acc[0], acc[1] + [col["label"]]]
        ),
        columns,
        [[], []],
    )
    [id_vars, value_vars] = cs

    # transform
    frames = pd.DataFrame(data.rows, columns=(id_vars + value_vars))
    frames = pd.melt(frames, id_vars=id_vars, value_vars=value_vars)

    # color scheme
    range_ = ["#66D3C3", "#2E678F"]

    # selections
    legend_selection = alt.selection_multi(fields=["variable"], bind="legend")
    click_selection = alt.selection_multi(encodings=["x"], empty="none")

    base = (
        alt.Chart(frames)
        .encode(
            alt.X(
                "ms:T",
                title=id_vars[0],
                axis=alt.Axis(format="%b %d", domain=False),
            ),
            alt.Y(
                "value:Q",
                title=data.title,
                stack=False,
                axis=alt.Axis(format=".2s", labelExpr="replace(datum.label, 'G', 'B')"),
            ),
            color=alt.Color(
                "variable:N",
                title="",
                scale=alt.Scale(range=range_),
                legend=alt.Legend(orient="left"),
            ),
            opacity=alt.condition(legend_selection, alt.value(0.65), alt.value(0.1)),
        )
        .transform_calculate(
            ms="datum.%s * 1000" % (id_vars[0]),
        )
    )

    area_chart = base.mark_area().add_selection(legend_selection)
    bar_chart = (
        base.mark_bar()
        .encode(
            opacity=alt.condition(click_selection, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("ms:T", title="Time", format="%Y-%m-%d %H:%M:%S"),
            ],
        )
        .add_selection(click_selection)
    )
    circle_chart = base.mark_point().encode(
        size=alt.value(64),
        opacity=alt.condition(click_selection, alt.value(1), alt.value(0)),
    )
    text_chart = base.mark_text(align="left", dx=8, dy=-8, fontSize=14).encode(
        text=alt.Text("value:N", format=",r"),
        color=alt.value("#333"),
        opacity=alt.condition(click_selection, alt.value(1), alt.value(0)),
    )

    st.altair_chart(
        (area_chart + bar_chart + circle_chart + text_chart).properties(height=400),
        use_container_width=True,
    )


# Side bar
with st.sidebar:
    st.markdown(
        (
            "- Use date range picker to change dates\n"
            "- Click on legend to filter\n"
            "- Click on graph to select a data point\n"
            "- Shift-Click on graph to select multiple\n"
            "- Click in empty spaces to deselect\n"
        )
    )


# Main dashboard


# Date-range dependent

date_range = st.date_input(
    "Date range",
    (datetime.date.today() - datetime.timedelta(days=7), datetime.date.today()),
)

if len(date_range) == 2:

    TOTAL_DAI_DATA_URL = (
        "https://scout.cool/supermax/api/v2/charts/preview/makerdao/mainnet/604fc93588a7c49b6445cd67"
        "?startdate=%s&enddate=%s" % date_range
    )

    SYSTEM_SURPLUS_BUFFER = (
        "https://scout.cool/supermax/api/v2/charts/preview/makerdao/mainnet/60513f2a6f910c0017cfd302"
        "?startdate=%s&enddate=%s" % date_range
    )

    make_area_chart((TOTAL_DAI_DATA_URL))

    make_area_chart((SYSTEM_SURPLUS_BUFFER))


else:
    st.write("Waiting on date range selection")
