"""
Roomalyzer is a Python module for visualizing conditions in your room.
"""
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import plotly.graph_objects as go


class Roomalyzer:
    """Roomalyzer class"""

    data = pd.DataFrame()
    dehum_log = pd.DataFrame()

    temp = "temperature"
    hum = "humidity"
    date = "date"
    __consts = {}

    def __init__(self):
        with open("constants.toml", "rb") as file:
            self.__consts = tomllib.load(file)

    @property
    def summary(self):
        """Data summary: global max, min, mean

        Returns
        -------
        pd.DataFrame
            Dataframe with calculated summary
        """
        return (
            self.data.agg(
                {self.temp: ["min", "max", "mean"], self.hum: ["min", "max", "mean"]}
            )
            .round(2)
            .reset_index()
        )

    def read_thingspeak(self, url: str):
        """Reads data from a ThingSpeak server

        Parameters
        ----------
        url : str
            URL to ThingSpeak server
        """
        df = (
            pd.json_normalize(requests.get(url, timeout=1000).json()["feeds"])
            .replace("NAN", np.nan)
            .dropna()
        )

        names = {"created_at": self.date, "field1": self.temp, "field2": self.hum}
        df = df.rename(columns=names)
        df[self.date] = pd.to_datetime(df[self.date])

        for item in [self.temp, self.hum]:
            df[item] = pd.to_numeric(df[item])

        df = df[df[self.temp] != 0]
        df = df[df[self.hum] != 0]

        self.data = df

    def read_dehumidifier_log(self, path: str, sep=","):
        """Reads file with dehumidifier on and off time, in csv format.

        Parameters
        ----------
        path : Path
            Path to .csv file
        sep : str, optional
            csv file separator, by default ","
        """
        try:
            df = pd.read_csv(Path(path), sep=sep)
            df["Date"] = pd.to_datetime(df["Date"])
            on = df[df["State"] == "on"]["Date"].rename("on").reset_index()
            off = df[df["State"] == "off"]["Date"].rename("off").reset_index()
            df = pd.concat([on, off], axis=1)
            self.dehum_log = df
        except FileNotFoundError:
            print("No dehumidifier log found. Omitting")

    def dehumidifier_state_to_bool(self):
        """Converts dehumidifier state from 'on' to 1 and 'off' to 0"""
        df = self.dehum_log.copy()
        df["State_b"] = np.where(df["State"] == "on", 1, 0)
        self.dehum_log = df

    def calc_average_vals(self, frequency: str, offset: str):
        """Calculates average values

        Parameters
        ----------
        frequency : str
            Can be day, month, week
        offset : str
            Shift regarding chosen frequency

        Returns
        -------
        pd.DataFrame
            Dataframe with averaged values
        """
        return (
            self.data.groupby(pd.Grouper(key=self.date, freq=frequency, offset=offset))
            .mean()
            .reset_index()
            .join(
                self.data.groupby(
                    pd.Grouper(key=self.date, freq=frequency, offset=offset)  # type: ignore
                )  # type: ignore
                .agg("std")
                .reset_index(),
                rsuffix="_std",
            )
            .dropna()
        )

    def check_humidity_levels(self):
        """Checks if humidity levels are off limits, adds a new column"""
        df = self.data.copy()

        def conditions(val):
            if val >= self.__consts["humidity_levels"]["high"]:
                return 1
            if val <= self.__consts["humidity_levels"]["low"]:
                return -1
            return 0

        func = np.vectorize(conditions)
        df["hum_lvl"] = func(df[self.hum])

        self.data = df

    def add_subplot_chart(
        self,
        figure: go.Figure,
        y_data: pd.Series,
        row: int,
        col: int,
        x_data=None,
        name=None,
        errorbars=None,
    ):
        """Adds a subplot chart

        Parameters
        ----------
        figure : go.Figure
            Figure to attach to
        y_data : pd.Series
            Data to put on Y axis
        row : int
            Row in subplot grid
        col : int
            Column in subplot grid
        x_data : pd.Series, optional
            Data to put on X axis, by default date and time
        name : str, optional
            Name of the chart, by default None
        errorbars : pd.Series, optional
            Data to create error bars, by default None

        Returns
        -------
        go.Figure
            Figure
        """
        if x_data is None:
            x_data = self.data[self.date]
        if name is None:
            name = y_data.name
        figure.append_trace(
            go.Scatter(
                x=x_data,
                y=y_data,
                name=name,
                error_y={"type": "data", "array": errorbars},
            ),
            row=row,
            col=col,
        )
        return figure

    def create_chart(self, y_data: pd.Series, x_data=None, name=None):
        """Create an indepentend chart

        Parameters
        ----------
        y_data : pd.Series
            Data to put on Y axis
        x_data : pd.Series, optional
            Data to put on X axis, by default None
        name : str, optional
            Name of the chart, by default None

        Returns
        -------
        go.Figure
            Figure with chart
        """
        if x_data is None:
            x_data = self.data[self.date]
        fig = go.Figure(data=go.Scatter(x=x_data, y=y_data, name=name))
        return fig

    def add_chart(
        self,
        figure: go.Figure,
        y_data: pd.Series,
        x_data=None,
        name=None,
        errorbars=None,
    ):
        """Append chart to an existing figure

        Parameters
        ----------
        figure : go.Figure
            Figure to append
        y_data : pd.Series
            Data to put on Y axis
        x_data : pd.Series, optional
            Data to put on X axis, by default None
        name : str, optional
            Name of the chart, by default None
        errorbars : pd.Series, optional
            Data to create error bars, by default None

        Returns
        -------
        go.Figure
            Figure
        """
        if x_data is None:
            x_data = self.data[self.date]
        figure = figure.add_trace(
            go.Scatter(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    name=name,
                    error_y={"type": "data", "array": errorbars},
                )
            )
        )
        return figure
