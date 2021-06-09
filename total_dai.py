import streamlit as st
import pandas as pd
import ssl
import altair as alt
import datetime
import functools
from flash_card import flash_card

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


def get_columns(data):
    columns = data["columns"]

    return functools.reduce(
        (
            lambda acc, col: [acc[0] + ["Date"], acc[1]]
            if col["label"] == "" or col["label"] == "Time"
            else [acc[0], acc[1] + [col["label"]]]
        ),
        columns,
        [[], []],
    )


def make_area_chart(url):
    data = load_data(url)
    st.subheader(data.title)

    [id_vars, value_vars] = get_columns(data)

    # transform
    frames = pd.DataFrame(data.rows, columns=(id_vars + value_vars))
    frames = pd.melt(frames, id_vars=id_vars, value_vars=value_vars)

    # color scheme
    range_ = ["#66D3C3", "#2E678F"]

    # selections
    legend_selection = alt.selection_multi(fields=["variable"], bind="legend")
    click_selection = alt.selection_multi(encodings=["x"], empty="none")
    scales = alt.selection_interval(bind="scales")

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

    area_chart = base.mark_area().add_selection(legend_selection, scales)
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


def make_bar_chart(url):
    data = load_data(url)
    st.subheader(data.title)

    [id_vars, value_vars] = get_columns(data)

    # transform
    frames = pd.DataFrame(data.rows, columns=(id_vars + value_vars))
    frames = pd.melt(frames, id_vars=id_vars, value_vars=value_vars)

    # st.write(frames)

    # color scheme
    range_ = ["#66D3C3", "#2E678F"]

    # selections
    legend_selection = alt.selection_multi(fields=["variable"], bind="legend")
    # click_selection = alt.selection_multi(on="mouseover", encodings=["x"], empty="none")
    scales = alt.selection_interval(bind="scales")

    base = (
        alt.Chart(frames)
        .encode(
            x=alt.X("variable", sort=value_vars, axis=None),
            y=alt.Y(
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
            column=alt.Column(
                "monthdate(ms):T",
                title="Date",
                spacing=4,
                header=alt.Header(labelOrient="bottom"),
            ),
            opacity=alt.condition(legend_selection, alt.value(1), alt.value(0.1)),
        )
        .transform_calculate(
            ms="datum.%s * 1000" % (id_vars[0]),
        )
    )

    bar_chart = (
        base.mark_bar(align="left")
        .encode(
            # opacity=alt.condition(click_selection, alt.value(1), alt.value(0.9)),
            tooltip=[
                alt.Tooltip("ms:T", title="Time", format="%Y-%m-%d %H:%M:%S"),
                alt.Tooltip("variable:O"),
                alt.Tooltip("value:Q"),
            ],
        )
        .add_selection(legend_selection, scales)
    )

    # text_chart = base.mark_text(
    #     width=40, align="left", dx=8, dy=-8, fontSize=14
    # ).encode(
    #     text=alt.Text("value:N", format=",r"),
    #     color=alt.value("#333"),
    #     opacity=alt.condition(click_selection, alt.value(1), alt.value(0)),
    # )

    st.altair_chart(
        bar_chart.properties(height=400),
    )


def make_pie_chart(url, category_name="category"):
    data = load_data(url)
    st.subheader(data.title)

    # transform
    frames = pd.DataFrame(data.rows, columns=[category_name, "value"])

    st.vega_lite_chart(
        frames,
        {
            "encoding": {
                "theta": {"field": "value", "type": "quantitative", "stack": True},
                "color": {"field": category_name, "type": "nominal"},
            },
            "layer": [
                {"mark": {"type": "arc", "outerRadius": 160, "tooltip": True}},
                # {
                #     "mark": {"type": "text", "radius": 180},
                #     "encoding": {"text": {"field": "value", "type": "nominal"}},
                # },
            ],
            # "view": {"stroke": "0"},
            "height": 400,
        },
        use_container_width=True,
    )


def make_big_text_card(url):
    data = load_data(url)

    [_, value_vars] = get_columns(data)

    st.subheader("%s (%s)" % (data.title, value_vars[0]))


    flash_card(
        data.title,
        primary_text=data["rows"][0][1],
        secondary_text=value_vars[0],
        formatter="0,0.00a",
        key="normal",
    )


with st.sidebar:
    date_range = st.date_input(
        "Date range",
        (datetime.date.today() - datetime.timedelta(days=7), datetime.date.today()),
    )

st.title("MAKERDAO")

# Main dashboard

TOTAL_COLLATERAL_DATA_URL = "https://scout.cool/supermax/api/v2/charts/preview/makerdao/mainnet/605ccdd5ab631d00174b5ec5"

COLLATERAL_BREAKDOWN_DATA_URL = "https://scout.cool/supermax/api/v2/charts/preview/makerdao/mainnet/6059225514aed9d410401758"

c1, c2 = st.beta_columns(2)
with c1:
    make_big_text_card(TOTAL_COLLATERAL_DATA_URL)

with c2:
    make_pie_chart(COLLATERAL_BREAKDOWN_DATA_URL, category_name="Currency")

# Date-range dependent


# with right_col:
#     st.text("\n\n\n")
#     with st.beta_expander("Instructions"):
#         st.markdown(
#             (
#                 "- Use date range picker to change dates\n"
#                 "- Click on legend to filter\n"
#                 "- Click on graph to select a data point\n"
#                 "- Shift-Click on graph to select multiple\n"
#                 "- Click in empty spaces to deselect\n"
#             )
#         )


if len(date_range) == 2:

    TOTAL_DAI_DATA_URL = (
        "https://scout.cool/supermax/api/v2/charts/preview/makerdao/mainnet/604fc93588a7c49b6445cd67"
        "?startdate=%s&enddate=%s" % date_range
    )

    SYSTEM_SURPLUS_BUFFER = (
        "https://scout.cool/supermax/api/v2/charts/preview/makerdao/mainnet/60513f2a6f910c0017cfd302"
        "?startdate=%s&enddate=%s" % date_range
    )

    WEEKLY_LIQUIDATED_COLLATERALS = (
        "https://scout.cool/supermax/api/v2/charts/preview/makerdao/mainnet/605902f564790b001782e8d4"
        "?startdate=%s&enddate=%s" % date_range
    )

    st.header("Overview")
    make_area_chart(TOTAL_DAI_DATA_URL)

    st.header("Liquidation")
    make_bar_chart(WEEKLY_LIQUIDATED_COLLATERALS)

    st.header("Supply and Withdraw")
    make_area_chart(SYSTEM_SURPLUS_BUFFER)


else:
    st.write("Waiting on date range selection")
