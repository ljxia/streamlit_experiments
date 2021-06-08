import streamlit as st
import pandas as pd
import ssl
import altair as alt
import datetime
import functools
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Project setup
st.set_page_config(page_title="Data table", page_icon=":coin:", layout="wide")


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
        (lambda acc, col: acc + [col["label"]]),
        columns,
        [],
    )


with st.sidebar:
    date_range = st.date_input(
        "Date range",
        (datetime.date.today() - datetime.timedelta(days=360), datetime.date.today()),
    )


if len(date_range) == 2:

    RECENT_TOKEN_URL = (
        "https://scout.cool/supermax/api/v2/charts/preview/polymathnetwork/mainnet/5cf57673716af1610d1a3831"
        "?startdate=%s&enddate=%s" % date_range
    )

    st.header("RECENT NEW TOKEN")

    data = load_data(RECENT_TOKEN_URL)
    st.subheader(data.title)

    cols = get_columns(data)
    df = pd.DataFrame(data.rows, columns=cols)

    st.write(df)

    # Infer basic colDefs from dataframe types
    gb = GridOptionsBuilder.from_dataframe(df)

    # customize gridOptions
    gb.configure_default_column(
        groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True
    )

    # date_getter_jscode = JsCode(
    #     """
    #     function(params) {
    #         return params.value
    #     };
    #     """
    # )
    # gb.configure_column(
    #     "Time",
    #     # type="dateColumnFilter",
    #     # type=["dateColumnFilter", "customDateTimeFormat"],
    #     valueGetter=date_getter_jscode,
    #     # custom_format_string="yyyy-MM-dd HH:mm zzz",
    # )

    gb.configure_side_bar()
    gb.configure_selection("multiple")
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_grid_options(domLayout="normal")
    gridOptions = gb.build()

    AgGrid(
        df,
        width="100%",
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,  # Set it to True to allow jsfunction to be injected
    )


else:
    st.write("Waiting on date range selection")
