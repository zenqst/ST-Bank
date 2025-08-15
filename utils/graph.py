import plotly.graph_objects as go

from database.core import db


async def create_graph() -> None:
    """
    Функция, которая создает график-файл public/charts/graph_main.png
    :return: None
    """

    data_st = await db.select_data("price_history", ["ts", "price"], {"coin_name": "st"}, fetch_all=True)
    data_v = await db.select_data("price_history", ["ts", "price"], {"coin_name": "v"}, fetch_all=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[item["ts"] for item in data_st],
        y=[item["price"] for item in data_st],
        name="ST"
    ))

    fig.add_trace(go.Scatter(
        x=[item["ts"] for item in data_v],
        y=[item["price"] for item in data_v],
        name="V"
    ))

    fig.update_layout(
        title="График курсов валют",
        xaxis_title="Дата",
        yaxis_title="Цена",
        legend_title="Валюта",
        template="simple_white",
    )

    fig.write_image("public/charts/graph_main.png", width=1920, height=1080)