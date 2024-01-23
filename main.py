"""aa"""
from dash import Dash, dcc, html, dash_table
import plotly.express as px
from plotly.subplots import make_subplots
from roomalyzer import Roomalyzer


ra = Roomalyzer()
app = Dash("Grzib")


def calculate_data():
    """Entry point"""

    ra.read_thingspeak(
        "https://api.thingspeak.com/channels/2394445/feeds.json?results=8000"
    )
    ra.read_dehumidifier_log("dehumidifier_log.csv")
    ra.check_humidity_levels()


def prepare_app():
    """Sets visual stuff, like plots and tables"""
    avg_day = ra.calc_average_vals("24H", offset="15H")
    print(avg_day)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
    fig = ra.add_subplot_chart(fig, ra.data[ra.temp], 1, 1, name="Temperature")
    fig = ra.add_subplot_chart(
        fig,
        avg_day[ra.temp],
        1,
        1,
        x_data=avg_day[ra.date],
        name="Średnia temperatura",
        errorbars=avg_day["temperature_std"],
    )
    fig.update_yaxes(title_text=r"$^\circ \text{C}$", row=1, col=1)

    fig = ra.add_subplot_chart(fig, ra.data[ra.hum], 2, 1, name="Humidity")
    fig = ra.add_subplot_chart(
        fig,
        avg_day[ra.hum],
        2,
        1,
        x_data=avg_day[ra.date],
        name="Średnia wilgotność",
        errorbars=avg_day["humidity_std"],
    )
    fig.update_yaxes(title_text=r"%RH", row=2, col=1)
    fig.update_layout(
        title="Temperatura i wilgotność",
        height=600,
        xaxis={"dtick": 86400000.0},
        xaxis2={"dtick": 86400000.0},
    )

    timeline = px.timeline(
        x_start=ra.dehum_log["on"],
        x_end=ra.dehum_log["off"],
        y=[1 for x in range(len(ra.dehum_log))],
    )
    timeline.update_layout(
        title="Praca osuszacza", yaxis_title="on/off", xaxis={"dtick": 86400000.0}
    )
    timeline.layout.yaxis.update(showticklabels=False)  # type: ignore
    timeline.layout.height = 250  # type: ignore

    app.layout = html.Div(
        [
            html.Div(children="Wrocław, Sienkiewicza"),
            dcc.Graph(id="figure", figure=fig, mathjax=True),
            dcc.Graph(id="timeline", figure=timeline),
            dash_table.DataTable(
                ra.summary.to_dict("records", index=True), fill_width=False
            ),
        ]
    )


if __name__ == "__main__":
    calculate_data()
    prepare_app()
    app.run(debug=False)
