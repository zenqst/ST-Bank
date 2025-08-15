import asyncio

import plotly.graph_objects as go
import plotly.express as px

from database.core import db


async def main():
    await db.connect()
    # data = await db.select_data("price_history", ["ts", "price"], {"coin_name": "st"}, fetch_all=True)
    # fig = px.line(data, x="ts", y="price")
    # fig.write_image("fig1.png")
    data_st = await db.select_data("price_history", ["ts", "price"], {"coin_name": "st"}, fetch_all=True)
    data_v = await db.select_data("price_history", ["ts", "price"], {"coin_name": "v"}, fetch_all=True)

    print(data_st, data_v)

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
    fig.show()
    fig.write_image("fig1.png", width=1920, height=1080)
    await db.close()


asyncio.run(main())