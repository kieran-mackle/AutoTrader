import os
import numpy as np
import pandas as pd
from math import pi
from typing import Union
from bokeh.models.annotations import Title
from bokeh.plotting import figure, output_file, show
from bokeh.io import output_notebook, curdoc
from bokeh.models import (
    CustomJS,
    ColumnDataSource,
    HoverTool,
    CrosshairTool,
    Span,
    CustomJSTransform,
)
from bokeh.layouts import gridplot, layout
from bokeh.transform import factor_cmap, cumsum, transform
from bokeh.palettes import Category20c, Turbo256
from autotrader.utilities import TradeAnalysis

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    import importlib_resources as pkg_resources
from . import package_data as pkgdata


# Ignore Bokeh warnings
import warnings

warnings.filterwarnings(action="ignore")


class AutoPlot:
    """Automated trading chart generator.

    Methods
    -------
    configure()
        Configure the plot settings.

    add_tool(tool_name)
        Add bokeh tool to plot. This adds the tool_name string to the fig_tools
        attribute.

    plot()
        Creates a trading chart of OHLC price data and indicators.

    """

    def __init__(self, data: Union[pd.DataFrame, pd.Series] = None):
        """Instantiates AutoPlot.

        Parameters
        ----------
        data : pd.DataFrame
            The OHLC price data to be charted.

        Returns
        -------
        None
            AutoPlot will be instantiated and ready for plotting.

        """
        self._chart_theme = "caliber"
        self._max_indis_over = 3
        self._max_indis_below = 2
        self._modified_data = None
        self._fig_tools = "pan,wheel_zoom,box_zoom,undo,redo,reset,save,crosshair"
        self._ohlc_height = 400
        self._ohlc_width = 800
        self._top_fig_height = 150
        self._bottom_fig_height = 150
        self._jupyter_notebook = False
        self._show_cancelled = True
        self._use_strat_plot_data = False
        self._line_chart = False

        # Modify data index
        if data is not None:
            if isinstance(data, pd.Series):
                self._data = self._reindex_data(data)
                self._backtest_data = None
                self._line_chart = True
            elif isinstance(data, pd.DataFrame):
                self._data = self._reindex_data(data)
                self._backtest_data = None
            else:
                raise Exception(
                    "Unrecognised data type pass to AutoPlot ({type(data)})"
                )

        # Load JavaScript code for auto-scaling
        self.autoscale_args = {}
        self._autoscale_code = pkg_resources.read_text(pkgdata, "autoscale.js")

    def add_tool(self, tool_name: str) -> None:
        """Adds a tool to the plot.

        Parameters
        ----------
        tool_name : str
            The name of tool to add (see Bokeh documentation).

        Returns
        -------
        None
            The tool will be added to the chart produced.

        """

        self._fig_tools = self._fig_tools + "," + tool_name

    def configure(
        self,
        max_indis_over: int = None,
        max_indis_below: int = None,
        fig_tools: str = None,
        ohlc_height: int = None,
        ohlc_width: int = None,
        top_fig_height: int = None,
        bottom_fig_height: int = None,
        jupyter_notebook: bool = None,
        show_cancelled: bool = None,
        chart_theme: str = None,
        use_strat_plot_data: bool = False,
    ) -> None:
        """Configures the plot settings.

        Parameters
        ----------
        max_indis_over : int, optional
            Maximum number of indicators overlaid on the main chart. The
            default is 3.

        max_indis_below : int, optional
            Maximum number of indicators below the main chart. The default is 2.

        fig_tools : str, optional
            The figure tools. The default is "pan,wheel_zoom,box_zoom,undo,
            redo,reset,save,crosshair".

        ohlc_height : int, optional
            The height (px) of the main chart. The default is 400.

        ohlc_width : int, optional
            The width (px) of the main chart. The default is 800.

        top_fig_height : int, optional
            The height (px) of the figure above the main chart. The default is 150.

        bottom_fig_height : int, optional
            The height (px) of the figure(s) below the main chart. The default is 150.

        jupyter_notebook : bool, optional
            Boolean flag when running in Jupyter Notebooks, to allow inline
            plotting. The default is False.

        show_cancelled : bool, optional
            Show/hide cancelled trades. The default is True.

        chart_theme : bool, optional
            The theme of the Bokeh chart generated. The default is "caliber".

        Returns
        -------
        None
            The plot settings will be saved to the active AutoTrader instance.

        """
        self._max_indis_over = (
            max_indis_over if max_indis_over is not None else self._max_indis_over
        )
        self._max_indis_below = (
            max_indis_below if max_indis_below is not None else self._max_indis_below
        )
        self._fig_tools = fig_tools if fig_tools is not None else self._fig_tools
        self._ohlc_height = (
            ohlc_height if ohlc_height is not None else self._ohlc_height
        )
        self._ohlc_width = ohlc_width if ohlc_width is not None else self._ohlc_width
        self._top_fig_height = (
            top_fig_height if top_fig_height is not None else self._top_fig_height
        )
        self._bottom_fig_height = (
            bottom_fig_height
            if bottom_fig_height is not None
            else self._bottom_fig_height
        )
        self._jupyter_notebook = (
            jupyter_notebook if jupyter_notebook is not None else jupyter_notebook
        )
        self._show_cancelled = (
            show_cancelled if show_cancelled is not None else self._show_cancelled
        )
        self._chart_theme = (
            chart_theme if chart_theme is not None else self._chart_theme
        )
        self._use_strat_plot_data = (
            use_strat_plot_data
            if use_strat_plot_data is not None
            else self._use_strat_plot_data
        )

    def plot(
        self,
        instrument: str = None,
        indicators: dict = None,
        trade_results: TradeAnalysis = None,
        show_fig: bool = True,
    ) -> None:
        """Creates a trading chart of OHLC price data and indicators.

        Extended Summary
        ----------------
        The following lists the keys corresponding to various indicators,
        which can be included in the chart using the indicators argument.

        over : over
            Generic line indicator over chart with key: data

        below : below
            Generic line indicator below chart with key: data

        MACD : below
            MACD indicator with keys: macd, signal, histogram

        MA : over
             Moving average overlay indicator with key: data

        RSI : below
            RSI indicator with key: data

        Heikin-Ashi : below
            Heikin Ashi candlesticks with key: data

        Supertrend : over
            Supertrend indicator with key: data

        Swings : over
            Swing levels indicator with key: data

        Engulfing : below
            Engulfing candlestick pattern with key: data

        Crossover : below
            Crossover indicator with key: data

        Grid : over
            Grid levels with key: data

        Pivot : over
            Pivot points with keys: data

        HalfTrend : over
            Halftrend indicator with key: data

        multi : below
            Multiple indicator type

        signals : over
            Trading signals plot with key: data

        bands : over
            Shaded bands indicator type

        threshold : below
            Threshold indicator type

        trading-session : over
            Highlighted trading session times with key: data

        bricks : below
            Price-based bricks with keys: data (DataFrame), timescale (bool)

        Parameters
        ----------
        instrument : str, optional
            The traded instrument name. The default is None.

        trade_results : TradeAnalysis, optional
            The TradeAnalysis results object. The default is None.

        indicators : dict, optional
            Indicators dictionary. The default is None.

        show_fig : bool, optional
            Flag to show the chart. The default is True.

        Returns
        -------
        None
            Calling this method will automatically generate and open a chart.

        See Also
        --------
        autotrader.autotrader.AutoTrader.analyse_backtest
        """

        # Preparation
        if trade_results is None:
            # Using Indiview
            if instrument is not None:
                title_string = f"AutoTrader IndiView - {instrument}"
            else:
                title_string = "AutoTrader IndiView"
            output_file("indiview-chart.html", title=title_string)

        else:
            # Plotting backtest results
            if instrument is None:
                instrument = trade_results.instruments_traded[0]
            title_string = (
                f"Backtest chart for {instrument} ({trade_results.interval} candles)"
            )
            formatted_instr = instrument.replace(os.sep, "_")
            output_file(
                f"{formatted_instr}-backtest-chart.html",
                title=f"AutoTrader Backtest Results - {instrument}",
            )

        # Add base data
        source = ColumnDataSource(self._data)

        # Main plot
        if self._use_strat_plot_data or self._line_chart:
            source.add(self._data.plot_data, "High")
            source.add(self._data.plot_data, "Low")
            main_plot = self._create_main_plot(source)
        else:
            source.add(
                (self._data["Close"] >= self._data["Open"])
                .values.astype(np.uint8)
                .astype(str),
                "change",
            )
            main_plot = self._plot_candles(source)

        # Initialise autoscale arguments
        self.autoscale_args = {"y_range": main_plot.y_range, "source": source}

        top_figs = []
        if trade_results is not None:
            account_hist = trade_results.account_history
            account_hist["data_index"] = self._data["data_index"]
            account_hist = self._interpolate_and_merge(account_hist)

            # if len(account_hist) != len(self._data):
            #     account_hist = self._interpolate_and_merge(account_hist)
            # else:
            #     # Need to add data_index column for plot to render NAV
            #     account_hist["data_index"] = self._data["data_index"]

            topsource = ColumnDataSource(account_hist)
            topsource.add(account_hist[["NAV", "equity"]].min(1), "Low")
            topsource.add(account_hist[["NAV", "equity"]].max(1), "High")

            # Get isolated position summary
            trade_summary = trade_results.trade_history
            order_summary = trade_results.order_history
            indicators = trade_results.indicators
            # open_trades = trade_results.open_isolated_positions
            cancelled_trades = trade_results.cancelled_orders

            top_fig = self._plot_lineV2(
                topsource,
                main_plot,
                "NAV",
                new_fig=True,
                legend_label="Net Asset Value",
            )
            # Add equity balance
            self._plot_lineV2(
                topsource,
                top_fig,
                "equity",
                legend_label="Account Balance",
                line_colour="blue",
            )

            # Add hover tool
            top_fig_hovertool = HoverTool(
                tooltips=[
                    ("Date", "@date{%b %d %H:%M}"),
                    ("Equity", "@{equity}{%0.2f}"),
                    ("NAV", "@{NAV}{%0.2f}"),
                ],
                formatters={
                    "@{equity}": "printf",
                    "@{NAV}": "printf",
                    "@date": "datetime",
                },
                mode="mouse",
            )
            top_fig.add_tools(top_fig_hovertool)

            # Append autoscale args
            self.autoscale_args["top_range"] = top_fig.y_range
            self.autoscale_args["top_source"] = topsource

            top_figs.append(top_fig)

            if not self._use_strat_plot_data:
                # Overlay trades
                # TODO - add way to visualise trades without candles
                self._plot_trade_history(
                    trade_summary, main_plot, order_summary=order_summary
                )
                if len(cancelled_trades) > 0 and self._show_cancelled:
                    self._plot_trade_history(
                        cancelled_trades, main_plot, cancelled_summary=True
                    )
                # if len(open_trades) > 0:
                #     self._plot_trade_history(open_trades, main_plot, open_summary=True)

        # Indicators
        bottom_figs = []
        if indicators is not None:
            bottom_figs = self._plot_indicators(indicators, main_plot)

        # Auto-scale y-axis of candlestick chart
        main_plot.x_range.js_on_change(
            "end", CustomJS(args=self.autoscale_args, code=self._autoscale_code)
        )

        # Compile plots for final figure
        plots = top_figs + [main_plot] + bottom_figs
        linked_crosshair = CrosshairTool(dimensions="both")

        titled = 0
        t = Title()
        t.text = title_string
        for plot in plots:
            if plot is not None:
                plot.xaxis.major_label_overrides = {
                    i: date.strftime("%b %d %Y")
                    for i, date in enumerate(pd.to_datetime(self._data["date"]))
                }
                plot.xaxis.bounds = (0, self._data.index[-1])
                plot.sizing_mode = "stretch_width"

                if titled == 0:
                    plot.title = t
                    titled = 1

                if plot.legend:
                    plot.legend.visible = True
                    plot.legend.location = "top_left"
                    plot.legend.border_line_width = 1
                    plot.legend.border_line_color = "#333333"
                    plot.legend.padding = 5
                    plot.legend.spacing = 0
                    plot.legend.margin = 0
                    plot.legend.label_text_font_size = "8pt"
                    plot.legend.click_policy = "hide"

                plot.add_tools(linked_crosshair)
                plot.min_border_left = 0
                plot.min_border_top = 3
                plot.min_border_bottom = 6
                plot.min_border_right = 10
                plot.outline_line_color = "black"

        # Construct final figure
        fig = gridplot(
            plots,
            ncols=1,
            toolbar_location="right",
            toolbar_options=dict(logo=None),
            merge_tools=True,
        )
        fig.sizing_mode = "stretch_width"

        # Set theme
        curdoc().theme = self._chart_theme

        if show_fig:
            if self._jupyter_notebook:
                output_notebook()
            show(fig)

    def _reindex_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Resets index of data to obtain integer indexing."""
        if isinstance(data, pd.Series):
            modified_data = data.to_frame(name="plot_data")
        else:
            modified_data = data.copy()
        modified_data["date"] = modified_data.index
        modified_data = modified_data.reset_index(drop=True)
        modified_data["data_index"] = modified_data.index
        return modified_data

    def _resample_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Resamples data to match the time index of the base data."""
        return data.reindex(self._data.date, method="ffill")

    def _check_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Checks the length of the inputted data against the base data,
        and resamples it if necessary.
        """
        if len(data) != len(self._data):
            data = self._resample_data(data)
        return data

    def _merge_data(self, data: pd.DataFrame, name=None) -> pd.DataFrame:
        """Merges the provided data with the base data, using the data of the
        base data and the index of the data to be merged.

        Parameters:
            data: the data to be merged
            name: the desired column name of the merged data
        """
        if isinstance(data, pd.Series):
            if data.name is None:
                data.name = "name"

        merged_data = pd.merge(
            self._data, data, left_on="date", right_index=True
        ).fillna("")

        if name is not None:
            merged_data.rename(columns={data.name: name}, inplace=True)

        return merged_data

    def _interpolate_and_merge(self, df):
        dt_data = self._data.set_index("date")
        concat_data = pd.concat([dt_data, df]).sort_index()

        # Check for timezone
        if self._data["date"][0].tz is not None:
            # TODO - improve how timezones are handled, this is gross
            concat_data.index = pd.to_datetime(concat_data.index, utc=True)

        interp_data = concat_data.interpolate(method="nearest").bfill()
        merged_data = self._merge_data(interp_data).drop_duplicates()
        merged_data = merged_data.replace("", np.nan).ffill()
        merged_data["data_index"] = merged_data.index
        return merged_data[list(df.columns) + ["date", "data_index"]].set_index("date")

    def _add_to_autoscale_args(self, source, y_range):
        """

        Parameters
        ----------
        source : ColumnDataSource
            The column data source.

        y_range : Bokeh Range
            The y_range attribute of the chart.

        """
        added = False
        range_key = "bot_range_1"
        source_key = "bot_source_1"
        while not added:
            if range_key not in self.autoscale_args:
                # Keys can be added
                self.autoscale_args[range_key] = y_range
                self.autoscale_args[source_key] = source
                added = True
            else:
                # Increment key
                range_key = range_key[:-1] + str(int(range_key[-1]) + 1)
                source_key = source_key[:-1] + str(int(source_key[-1]) + 1)

    def _add_backtest_price_data(self, backtest_price_data: pd.DataFrame) -> None:
        """Processes backtest price data to included integer index of base
        data.
        """
        temp_data = self._data.copy()
        temp_data.index = temp_data["date"]

        self._backtest_data = temp_data.reindex(
            backtest_price_data.index, method="ffill"
        )

    def _portfolio_plot(self, trade_results: TradeAnalysis):
        """Creates a positions history chart."""
        # Extract results
        account_history = self._reindex_data(trade_results.account_history)
        position_history = self._reindex_data(np.sign(trade_results.position_history))
        no_instruments = len(trade_results.instruments_traded)
        # iso_pos_history = self._reindex_data(trade_results.isolated_position_history)
        # iso_pos_history = iso_pos_history[iso_pos_history["status"] == "closed"]

        # Plot account balance history
        topsource = ColumnDataSource(account_history)
        topsource.add(account_history[["NAV", "equity"]].min(1), "Low")
        topsource.add(account_history[["NAV", "equity"]].max(1), "High")

        navfig = figure(
            width=self._ohlc_width,
            height=self._top_fig_height,
            title="Account History",
            active_drag="pan",
            active_scroll="wheel_zoom",
        )
        navfig.line(
            x="data_index",
            y="NAV",
            line_color="black",
            legend_label="Backtest Net Asset Value",
            source=topsource,
        )
        navfig.line(
            x="data_index",
            y="equity",
            line_color="blue",
            legend_label="Backtest Equity",
            source=topsource,
        )
        navfig.ray(
            x=[0],
            y=account_history["NAV"][0],
            length=len(account_history),
            angle=0,
            line_width=0.5,
            line_color="black",
        )

        fill_color = pd.Series(dtype=str, index=account_history.index)
        nav0 = account_history["NAV"][0]
        fill_color[account_history["NAV"] >= nav0] = "green"
        fill_color[account_history["NAV"] < nav0] = "red"

        fill_alpha = 0.3

        navfig.varea(
            x="data_index",
            y1=transform(
                "NAV",
                CustomJSTransform(
                    v_func=f"return xs.map(x => x > {nav0} ? x : {nav0})"
                ),
            ),
            y2=nav0,
            source=topsource,
            color="limegreen",
            fill_alpha=fill_alpha,
        )

        navfig.varea(
            x="data_index",
            y1=transform(
                "NAV",
                CustomJSTransform(
                    v_func=f"return xs.map(x => x < {nav0} ? x : {nav0})"
                ),
            ),
            y2=nav0,
            source=topsource,
            color="salmon",
            fill_alpha=fill_alpha,
        )

        # Add hover tool
        navfig_hovertool = HoverTool(
            tooltips=[
                ("Date", "@date{%b %d %H:%M}"),
                ("Equity", "$@{equity}{%0.2f}"),
                ("NAV", "$@{NAV}{%0.2f}"),
            ],
            formatters={
                "@{equity}": "printf",
                "@{NAV}": "printf",
                "@date": "datetime",
            },
            mode="mouse",
        )
        navfig.add_tools(navfig_hovertool)

        # Add to autoscale args
        self.autoscale_args = {"y_range": navfig.y_range, "source": topsource}

        # Create colour pallete
        if no_instruments < 3:
            colors = Category20c[3][0:no_instruments]
        elif no_instruments <= 20:
            colors = Category20c[no_instruments]
        else:
            colors = Turbo256[:no_instruments]

        if trade_results.price_history is not None:
            # Match price history index to position history
            price_hist = trade_results.price_history.reindex(
                trade_results.position_history.index
            )

            # Multiply position history by prices to get values
            position_values = (price_hist * trade_results.position_history).abs()

            # Normalise values to % of total
            position_values = position_values.div(
                position_values.sum(axis=1).values, axis=0
            ).fillna(value=0)

            # Create source
            pos_vals = self._reindex_data(position_values)[position_values.columns]
            compsource = ColumnDataSource(pos_vals)

            # Plot portfolio composition history
            # compfig = figure(
            #     width=self._ohlc_width,
            #     height=self._top_fig_height,
            #     title="Portfolio Composition History",
            #     x_range=navfig.x_range,
            #     y_range=(0, 1),
            #     active_drag="pan",
            #     active_scroll="xwheel_zoom",
            #     tools="pan,xwheel_zoom,hover,box_zoom",
            #     tooltips="$name",
            # )
            # compfig.varea_stack(
            #     stackers=position_values.columns,
            #     x="index",
            #     source=compsource,
            #     color=colors,
            # )
            # compfig = [compfig]
            compfig = []
        else:
            compfig = []

        # Plot leverage history
        leverage = (
            account_history["open_interest"] / account_history["equity"]
        ).to_frame("leverage")
        leverage["Low"] = leverage[["leverage"]].min(1)
        leverage["High"] = leverage[["leverage"]].max(1)
        levsource = ColumnDataSource(leverage)

        levfig = figure(
            width=self._ohlc_width,
            height=self._top_fig_height,
            title="Leverage Utilisation History",
            active_drag="pan",
            active_scroll="wheel_zoom",
            x_range=navfig.x_range,
        )
        levfig.line(
            x="index",
            y="leverage",
            line_color="blue",
            source=levsource,
        )

        self._add_to_autoscale_args(levsource, levfig.y_range)

        # Plot positions
        pos_source = ColumnDataSource(position_history)
        pos_source.add(np.ones(len(position_history)) * -1.1, "Low")
        pos_source.add(np.ones(len(position_history)) * 1.1, "High")
        position_figs = []
        max_pos_charts = self._max_indis_below
        for n, instrument in enumerate(trade_results.instruments_traded):
            if n < max_pos_charts:
                posfig = figure(
                    width=self._ohlc_width,
                    height=self._top_fig_height,
                    title=f"{instrument} Position History",
                    active_drag="pan",
                    active_scroll="wheel_zoom",
                    x_range=navfig.x_range,
                )
                posfig.line(
                    x="data_index",
                    y=instrument,
                    line_color="blue",
                    source=pos_source,
                )
                position_figs.append(posfig)

                self._add_to_autoscale_args(pos_source, posfig.y_range)

        # Add javascript callback
        js = CustomJS(args=self.autoscale_args, code=self._autoscale_code)
        navfig.x_range.js_on_change("end", js)

        # Construct final figure
        plots = [navfig, levfig] + compfig + position_figs

        for plot in plots:
            plot.sizing_mode = "stretch_width"
            plot.min_border_left = 0
            plot.min_border_top = 3
            plot.min_border_bottom = 6
            plot.min_border_right = 10
            plot.outline_line_color = "black"

            if plot.legend:
                plot.legend.visible = True
                plot.legend.location = "top_left"
                plot.legend.border_line_width = 1
                plot.legend.border_line_color = "#333333"
                plot.legend.padding = 5
                plot.legend.spacing = 0
                plot.legend.margin = 0
                plot.legend.label_text_font_size = "8pt"
                plot.legend.click_policy = "hide"

            plot.xaxis.bounds = (0, account_history.index[-1])
            plot.xaxis.major_label_overrides = {
                i: date.strftime("%b %d %Y")
                for i, date in enumerate(pd.to_datetime(account_history["date"]))
            }

        # Pie chart of trades per instrument
        trades_per_instrument = [
            sum(trade_results.trade_history["instrument"] == inst)
            for inst in trade_results.instruments_traded
        ]
        pie_data = pd.DataFrame(
            data={"trades": trades_per_instrument},
            index=trade_results.instruments_traded,
        ).fillna(0)
        pie_data["angle"] = pie_data["trades"] / pie_data["trades"].sum() * 2 * pi
        pie_data["color"] = colors
        pie = self._plot_pie(pie_data, fig_title="Trade Distribution")

        pie.axis.axis_label = None
        pie.axis.visible = False
        pie.grid.grid_line_color = None
        pie.sizing_mode = "stretch_width"
        pie.legend.location = "top_left"
        pie.legend.border_line_width = 1
        pie.legend.border_line_color = "#333333"
        pie.legend.padding = 5
        pie.legend.spacing = 0
        pie.legend.margin = 0
        pie.legend.label_text_font_size = "8pt"

        # Plot returns distribution (across all positions)
        # isopos_returns = (
        #     iso_pos_history.direction
        #     * (iso_pos_history.exit_price - iso_pos_history.fill_price)
        #     / iso_pos_history.fill_price
        # )
        # h, edges = np.histogram(
        #     isopos_returns, bins=max(10, int(0.1 * len(isopos_returns)))
        # )
        # returnsfig = figure(
        #     title="Distribution of Returns",
        #     toolbar_location=None,
        #     height=250,
        # )
        # returnsfig.quad(
        #     top=h,
        #     bottom=0,
        #     left=edges[:-1],
        #     right=edges[1:],
        # )
        # returnsfig.sizing_mode = "stretch_width"

        subfig = gridplot(
            plots,
            ncols=1,
            toolbar_location="right",
            toolbar_options=dict(logo=None),
            merge_tools=True,
        )
        fig = layout(
            [
                [subfig],
                [pie],  # , returnsfig],
            ],
        )
        fig.sizing_mode = "scale_width"

        curdoc().theme = self._chart_theme

        if self._jupyter_notebook:
            output_notebook()
        show(fig)

    def _plot_indicators(self, indicators: dict, linked_fig):
        """Plots indicators based on indicator type. If inidcator type is
        "over", it will be plotted on top of linked_fig. If indicator type is
        "below", it will be plotted on a new figure below the OHLC chart.
        """
        x_range = self._data.index
        plot_type = {
            "MACD": "below",
            "MA": "over",
            "RSI": "below",
            "STOCHASTIC": "below",
            "Heikin-Ashi": "below",
            "Supertrend": "over",
            "Swings": "over",
            "Engulfing": "below",
            "Crossover": "below",
            "over": "over",
            "below": "below",
            "Grid": "over",
            "Pivot": "over",
            "HalfTrend": "over",
            "multi": "below",
            "signals": "over",
            "bands": "over",
            "threshold": "below",
            "trading-session": "over",
            "bricks": "below",
            "PSAR": "over",
            "bars": "below",
        }

        # Plot indicators
        indis_over = 0
        indis_below = 0
        bottom_figs = []
        colours = ["red", "blue", "orange", "green", "black", "yellow"]

        for indicator in indicators:
            indi_type = indicators[indicator]["type"]

            if indi_type in plot_type:
                # The indicator plot type is recognised
                if (
                    plot_type[indi_type] == "over"
                    and indis_over < self._max_indis_over
                    and not self._use_strat_plot_data
                ):
                    if indi_type == "Supertrend":
                        self._plot_supertrend(indicators[indicator]["data"], linked_fig)
                        indis_over += 1  # Count as 2 indicators
                    elif indi_type == "HalfTrend":
                        self._plot_halftrend(indicators[indicator]["data"], linked_fig)
                        indis_over += 1  # Count as 2 indicators
                    elif indi_type == "Swings":
                        self._plot_swings(indicators[indicator]["data"], linked_fig)
                    elif indi_type == "Grid":
                        self._plot_grid(indicators[indicator]["data"], linked_fig)
                    elif indi_type == "Pivot":
                        self._plot_pivot_points(indicators[indicator], linked_fig)
                    elif indi_type == "signals":
                        self._plot_signals(linked_fig, indicators[indicator]["data"])

                    elif indi_type == "bands":
                        self._plot_bands(
                            indicators[indicator],
                            linked_fig=linked_fig,
                            new_fig=False,
                            legend_label=indicator,
                        )

                    elif indi_type == "trading-session":
                        self._plot_trading_session(indicators[indicator], linked_fig)

                    elif indi_type == "PSAR":
                        self._plot_scatter(
                            linked_fig,
                            indicators[indicator]["data"],
                            legend_label=indicator,
                        )

                    else:
                        # Generic overlay indicator - plot as line
                        if isinstance(indicators[indicator]["data"], pd.Series):
                            # Timeseries provided, merge indexes
                            if indicators[indicator]["data"].name is None:
                                indicators[indicator]["data"].name = "data"
                            merged_indicator_data = pd.merge(
                                self._data,
                                indicators[indicator]["data"],
                                left_on="date",
                                right_index=True,
                            )
                            line_data = merged_indicator_data[
                                indicators[indicator]["data"].name
                            ]
                            x_vals = line_data.index
                            y_vals = line_data.values
                        else:
                            raise Exception("Plot data must be a timeseries.")

                        linked_fig.line(
                            x_vals,
                            y_vals,
                            line_width=1.5,
                            legend_label=indicator,
                            line_color=(
                                indicators[indicator]["color"]
                                if "color" in indicators[indicator]
                                else colours[indis_over]
                            ),
                        )
                    indis_over += 1

                elif (
                    plot_type[indi_type] == "below"
                    and indis_below < self._max_indis_below
                ):
                    if indi_type == "MACD":
                        new_fig = self._plot_macd(
                            x_range, indicators[indicator], linked_fig
                        )
                        new_fig.title = indicator

                    elif indi_type == "Heikin-Ashi":
                        HA_data = self._reindex_data(indicators[indicator]["data"])
                        source = ColumnDataSource(HA_data)
                        source.add(
                            (HA_data.Close >= HA_data.Open)
                            .values.astype(np.uint8)
                            .astype(str),
                            "change",
                        )
                        new_fig = self._plot_candles(source)
                        new_fig.x_range = linked_fig.x_range
                        new_fig.y_range = linked_fig.y_range
                        new_fig.title = indicator
                        indis_below += (
                            self._max_indis_below
                        )  # To block any other new plots below.

                    elif indi_type == "RSI":
                        new_fig = self._plot_line(
                            indicators[indicator]["data"],
                            linked_fig,
                            legend_label=indicator,
                            new_fig=True,
                        )
                        if "swings" in indicators[indicator]:
                            self._plot_swings(indicators[indicator]["swings"], new_fig)
                    elif indi_type == "bricks":
                        timescale = (
                            indicators[indicator]["timescale"]
                            if "timescale" in indicators[indicator]
                            else False
                        )
                        new_fig = self._plot_bricks(
                            indicators[indicator]["data"], linked_fig, timescale
                        )

                    elif indi_type == "multi":
                        # Plot multiple lines on the same figure
                        new_fig = figure(
                            width=linked_fig.width,
                            height=130,
                            title=indicator,
                            tools=linked_fig.tools,
                            active_drag=linked_fig.tools[0],
                            active_scroll=linked_fig.tools[1],
                            x_range=linked_fig.x_range,
                        )

                        for dataset in list(indicators[indicator].keys())[1:]:
                            if (
                                type(indicators[indicator][dataset]["data"])
                                == pd.Series
                            ):
                                # Merge indexes
                                data_name = "plot_data"
                                indicators[indicator][dataset]["data"].name = data_name
                                merged_indicator_data = pd.merge(
                                    self._data,
                                    indicators[indicator][dataset]["data"],
                                    left_on="date",
                                    right_index=True,
                                )
                                line_data = merged_indicator_data[data_name]
                                x_vals = line_data.index
                                y_vals = line_data.values
                            else:
                                raise Exception("Plot data must be a timeseries.")

                            new_fig.line(
                                x_vals,
                                y_vals,
                                line_color=(
                                    indicators[indicator][dataset]["color"]
                                    if "color" in indicators[indicator][dataset]
                                    else "black"
                                ),
                                legend_label=dataset,
                            )

                    elif indi_type == "threshold":
                        new_fig = self._plot_bands(
                            indicators[indicator],
                            linked_fig=linked_fig,
                            legend_label=indicator,
                        )

                    elif indi_type == "bars":
                        frame = indicators[indicator]["data"].to_frame()
                        frame["color"] = "grey"
                        source = self._create_line_source(indicators[indicator]["data"])

                        # Add color to data
                        source.add(frame["color"].values, "color")

                        new_fig = self._plot_bars(
                            0,
                            "plot_data",
                            source,
                            linked_fig=linked_fig,
                            fig_height=self._bottom_fig_height,
                            hover_name="plot_data",
                        )

                    else:
                        # Generic indicator - plot as line
                        if isinstance(indicators[indicator]["data"], pd.Series):
                            # Timeseries provided, merge indexes
                            if indicators[indicator]["data"].name is None:
                                indicators[indicator]["data"].name = "data"
                            line_source = self._create_line_source(
                                indicators[indicator]["data"]
                            )
                        else:
                            raise Exception("Plot data must be a timeseries.")

                        new_fig = self._plot_lineV2(
                            line_source,
                            linked_fig,
                            indicators[indicator]["data"].name,
                            new_fig=True,
                            legend_label=indicator,
                            fig_height=130,
                        )
                        self._add_to_autoscale_args(line_source, new_fig.y_range)

                    indis_below += 1
                    bottom_figs.append(new_fig)
            else:
                # The indicator plot type is not recognised - plotting on new fig
                if indis_below < self._max_indis_below:
                    print(
                        "Indicator type '{}' not recognised in AutoPlot.".format(
                            indi_type
                        )
                    )
                    line_source = self._create_line_source(
                        indicators[indicator]["data"]
                    )
                    new_fig = self._plot_lineV2(
                        line_source,
                        linked_fig,
                        indicators[indicator]["data"].name,
                        new_fig=True,
                        legend_label=indicators[indicator]["data"].name,
                        fig_height=130,
                    )
                    self._add_to_autoscale_args(line_source, new_fig.y_range)

                    indis_below += 1
                    bottom_figs.append(new_fig)

        return bottom_figs

    def _create_line_source(self, indicator_data):
        """Create ColumndDataSource from indicator line data."""
        # Overwrite indicator data name to prevent conflict
        data_name = "plot_data"
        indicator_data.name = data_name
        merged_indicator_data = pd.merge(
            self._data, indicator_data, left_on="date", right_index=True
        )
        merged_indicator_data.fillna(method="bfill", inplace=True)
        data_name = indicator_data.name
        line_source = ColumnDataSource(merged_indicator_data[[data_name, "data_index"]])
        line_source.add(merged_indicator_data[data_name].values, "High")
        line_source.add(merged_indicator_data[data_name].values, "Low")
        return line_source

    def _create_main_plot(
        self,
        source: ColumnDataSource,
        line_colour: str = "black",
        legend_label: str = "Data",
    ):
        fig = figure(
            width=self._ohlc_width,
            height=self._ohlc_height,
            title="Custom Plot Data",
            tools=self._fig_tools,
            active_drag="pan",
            active_scroll="wheel_zoom",
        )

        fig.line(
            "data_index",
            "plot_data",
            line_color=line_colour,
            # legend_label = legend_label,
            source=source,
        )

        return fig

    def _plot_lineV2(
        self,
        source: ColumnDataSource,
        linked_fig,
        column: str,
        new_fig: bool = False,
        fig_height: float = 150,
        fig_title: str = None,
        legend_label: str = None,
        line_colour: str = "black",
    ):
        """Generic method to plot data as a line."""
        # Initiate figure
        if new_fig:
            fig = figure(
                width=linked_fig.width,
                height=fig_height,
                title=fig_title,
                tools=self._fig_tools,
                active_drag="pan",
                active_scroll="wheel_zoom",
                x_range=linked_fig.x_range,
            )
        else:
            fig = linked_fig

        fig.line(
            "data_index",
            column,
            line_color=line_colour,
            legend_label=legend_label,
            source=source,
        )

        return fig

    def _plot_line(
        self,
        plot_data,
        linked_fig,
        new_fig=False,
        fig_height=150,
        fig_title=None,
        legend_label=None,
        hover_name=None,
        line_colour="black",
    ):
        """Generic method to plot data as a line."""

        # Initiate figure
        if new_fig:
            fig = figure(
                width=linked_fig.width,
                height=fig_height,
                title=fig_title,
                tools=self._fig_tools,
                active_drag="pan",
                active_scroll="wheel_zoom",
                x_range=linked_fig.x_range,
            )
        else:
            fig = linked_fig

        # Add glyphs
        if len(plot_data) != len(self._data):
            # Mismatched timeframe
            merged_data = self._merge_data(plot_data, name="plot_data")
            source = ColumnDataSource(merged_data)
        else:
            source = ColumnDataSource(self._data)
            source.add(plot_data, "plot_data")

        fig.line(
            "data_index",
            "plot_data",
            line_color=line_colour,
            legend_label=legend_label,
            source=source,
        )

        if hover_name is not None:
            fig_hovertool = HoverTool(
                tooltips=[
                    ("Date", "@date{%b %d %H:%M}"),
                    (hover_name, "@{plot_data}{%0.2f}"),
                ],
                formatters={"@{plot_data}": "printf", "@date": "datetime"},
                mode="vline",
            )

            fig.add_tools(fig_hovertool)

        return fig

    def _plot_scatter(
        self,
        linked_fig,
        data,
        new_fig=False,
        fig_height=150,
        fig_title=None,
        legend_label=None,
    ):
        """Creates a scatter plot."""
        # Initiate figure
        if new_fig:
            fig = figure(
                width=linked_fig.width,
                height=fig_height,
                title=fig_title,
                tools=self._fig_tools,
                active_drag="pan",
                active_scroll="wheel_zoom",
                x_range=linked_fig.x_range,
            )
        else:
            fig = linked_fig

        # Add glyphs
        merged_data = self._merge_data(data, "plot_data")
        source = ColumnDataSource(merged_data)
        fig.circle("data_index", "plot_data", legend_label=legend_label, source=source)

    def _plot_candles(self, source):
        """Plots OHLC data onto new figure."""
        bull_colour = "#D5E1DD"
        bear_colour = "#F2583E"
        candle_colours = [bear_colour, bull_colour]
        colour_map = factor_cmap("change", candle_colours, ["0", "1"])

        candle_tooltips = [
            ("Date", "@date{%b %d %H:%M:%S}"),
            # ("Open", "@Open{0.0000}"),
            # ("High", "@High{0.0000}"),
            # ("Low", "@Low{0.0000}"),
            ("Close", "@Close{0.0000}"),
        ]

        candle_plot = figure(
            width=self._ohlc_width,
            height=self._ohlc_height,
            tools=self._fig_tools,
            active_drag="pan",
            active_scroll="wheel_zoom",
        )

        candle_plot.segment(
            "index", "High", "index", "Low", color="black", source=source
        )
        candles = candle_plot.vbar(
            "index",
            0.7,
            "Open",
            "Close",
            source=source,
            line_color="black",
            fill_color=colour_map,
        )

        candle_hovertool = HoverTool(
            tooltips=candle_tooltips,
            formatters={"@date": "datetime"},
            mode="vline",
            renderers=[candles],
        )

        candle_plot.add_tools(candle_hovertool)

        return candle_plot

    def _plot_bricks(self, data, linked_fig, timescale: bool = False):
        """Plots bricks onto new figure."""
        if timescale:
            data = pd.merge(
                self._data[["date", "data_index"]],
                data,
                left_on="date",
                right_index=True,
            ).dropna()
            xrange = linked_fig.x_range
        else:
            data.reset_index(drop=True, inplace=True)
            xrange = None
        source = ColumnDataSource(data)
        source.add(
            (data.Close >= data.Open).values.astype(np.uint8).astype(str), "change"
        )

        bull_colour = "#D5E1DD"
        bear_colour = "#F2583E"
        candle_colours = [bear_colour, bull_colour]
        colour_map = factor_cmap("change", candle_colours, ["0", "1"])

        candle_tooltips = [("Open", "@Open{0.0000}"), ("Close", "@Close{0.0000}")]

        candle_plot = figure(
            width=self._ohlc_width,
            height=self._ohlc_height,
            tools=self._fig_tools,
            active_drag="pan",
            active_scroll="wheel_zoom",
            x_range=xrange,
        )

        candles = candle_plot.vbar(
            "index",
            0.7,
            "Open",
            "Close",
            source=source,
            line_color="black",
            fill_color=colour_map,
        )

        candle_hovertool = HoverTool(
            tooltips=candle_tooltips,
            formatters={"@date": "datetime"},
            mode="vline",
            renderers=[candles],
        )

        candle_plot.add_tools(candle_hovertool)

        if timescale:
            # Define autoscale arguments
            source.add(np.maximum(data["Close"], data["Open"]), "High")
            source.add(np.minimum(data["Close"], data["Open"]), "Low")
            self._add_to_autoscale_args(source, candle_plot.y_range)

        return candle_plot

    def _plot_swings(self, swings, linked_fig):
        """Plots swing detection indicator."""
        swings = pd.merge(self._data, swings, left_on="date", right_index=True).fillna(
            ""
        )

        linked_fig.scatter(
            list(swings.index),
            list(swings.Last.values),
            marker="dash",
            size=15,
            fill_color="black",
            legend_label="Last Swing Price Level",
        )

    def _plot_supertrend(self, st_data, linked_fig):
        """Plots supertrend indicator."""
        # Extract supertrend data
        # uptrend     = st_data['uptrend']
        # dntrend     = st_data['downtrend']

        # reset index
        st_data["date"] = st_data.index
        st_data = st_data.reset_index(drop=True)

        # Add glyphs
        linked_fig.scatter(
            st_data.index,
            st_data["uptrend"],
            size=5,
            fill_color="blue",
            legend_label="Up trend support",
        )
        linked_fig.scatter(
            st_data.index,
            st_data["downtrend"],
            size=5,
            fill_color="red",
            legend_label="Down trend support",
        )

    def _plot_halftrend(self, htdf, linked_fig):
        """Plots halftrend indicator."""
        # reset index
        htdf["date"] = htdf.index
        htdf = htdf.reset_index(drop=True)
        long_arrows = htdf[htdf.buy != 0]
        short_arrows = htdf[htdf.sell != 0]

        # Add glyphs
        linked_fig.scatter(
            htdf.index,
            htdf["atrLow"],
            size=3,
            fill_color="blue",
            legend_label="ATR Support",
        )
        linked_fig.scatter(
            htdf.index,
            htdf["atrHigh"],
            size=3,
            fill_color="red",
            legend_label="ATR Resistance",
        )
        linked_fig.line(htdf.index, htdf["atrLow"], line_color="blue")
        linked_fig.line(htdf.index, htdf["atrHigh"], line_color="red")

        # Add buy and sell entry signals
        self._plot_trade(
            long_arrows.index,
            long_arrows.atrLow,
            "triangle",
            "green",
            "Buy Signals",
            linked_fig,
            10,
        )
        self._plot_trade(
            short_arrows.index,
            short_arrows.atrHigh,
            "inverted_triangle",
            "red",
            "Sell Signals",
            linked_fig,
            10,
        )

    def _plot_signals(self, linked_fig, signals_df):
        """Plots long and short entry signals over OHLC chart."""

        signals_df = signals_df.reset_index(drop=True)
        long_arrows = signals_df[signals_df["buy"] != 0]
        short_arrows = signals_df[signals_df["sell"] != 0]

        # Add buy and sell entry signals
        self._plot_trade(
            long_arrows.index,
            long_arrows.buy,
            "triangle",
            "lightgreen",
            "Buy Signals",
            linked_fig,
            12,
        )
        self._plot_trade(
            short_arrows.index,
            short_arrows.sell,
            "inverted_triangle",
            "orangered",
            "Sell Signals",
            linked_fig,
            12,
        )

    def _plot_grid(self, grid_levels, linked_fig, linewidth=0.5):
        for price in grid_levels:
            hline = Span(
                location=price,
                dimension="width",
                line_color="black",
                line_dash="dashed",
                line_width=linewidth,
            )
            linked_fig.add_layout(hline)

    def _plot_pivot_points(self, pivot_dict, linked_fig, levels=1):
        """Adds pivot points to OHLC chart."""
        pivot_df = pivot_dict["data"]
        levels = pivot_dict["levels"] if "levels" in pivot_dict else levels

        # Check pivot_df
        pivot_df = self._check_data(pivot_df)

        # Merge to integer index
        pivot_df = pd.merge(self._data, pivot_df, left_on="date", right_index=True)

        # Remove NaNs
        pivot_df = pivot_df.fillna("")

        linked_fig.scatter(
            list(pivot_df.index),
            list(pivot_df["pivot"].values),
            marker="dash",
            size=15,
            line_color="black",
            legend_label="Pivot",
        )

        if levels > 0:
            linked_fig.scatter(
                list(pivot_df.index),
                list(pivot_df["s1"].values),
                marker="dash",
                size=15,
                line_color="blue",
                legend_label="Support 1",
            )

            linked_fig.scatter(
                list(pivot_df.index),
                list(pivot_df["r1"].values),
                marker="dash",
                size=15,
                line_color="red",
                legend_label="Resistance 1",
            )

            if levels > 1:
                linked_fig.scatter(
                    list(pivot_df.index),
                    list(pivot_df["s2"].values),
                    marker="dot",
                    size=10,
                    line_color="blue",
                    legend_label="Support 2",
                )

                linked_fig.scatter(
                    list(pivot_df.index),
                    list(pivot_df["r2"].values),
                    marker="dot",
                    size=10,
                    line_color="red",
                    legend_label="Resistance 2",
                )

                if levels > 2:
                    linked_fig.scatter(
                        list(pivot_df.index),
                        list(pivot_df["s3"].values),
                        marker="dot",
                        size=7,
                        line_color="blue",
                        legend_label="Support 3",
                    )

                    linked_fig.scatter(
                        list(pivot_df.index),
                        list(pivot_df["r3"].values),
                        marker="dot",
                        size=7,
                        line_color="red",
                        legend_label="Resistance 3",
                    )

    def _plot_trading_session(self, session_plot_data, linked_fig):
        """Shades trading session times."""

        session = session_plot_data["data"].lower()
        fill_color = (
            session_plot_data["fill_color"]
            if "fill_color" in session_plot_data
            else "blue"
        )
        fill_alpha = (
            session_plot_data["fill_alpha"]
            if "fill_alpha" in session_plot_data
            else 0.3
        )
        line_color = (
            session_plot_data["line_color"]
            if "line_color" in session_plot_data
            else None
        )

        times = {
            "sydney": {"start": "21:00", "end": "05:00"},
            "london": {"start": "08:00", "end": "16:00"},
            "new york": {"start": "13:00", "end": "21:00"},
            "tokyo": {"start": "23:00", "end": "07:00"},
            "frankfurt": {"start": "07:00", "end": "15:00"},
        }

        index_data = self._data.set_index("date")

        midpoint = max(self._data.High.values)
        height = 2 * midpoint

        session_start = times[session]["start"]
        session_end = times[session]["end"]

        session_data = index_data.between_time(session_start, session_end)

        opens = session_data[
            session_data.data_index - session_data.data_index.shift(1) != 1
        ].data_index
        closes = session_data[
            (session_data.data_index - session_data.data_index.shift(1) != 1)
            .shift(-1)
            .fillna(True)
        ].data_index

        linked_fig.hbar(
            midpoint,
            height,
            opens,
            closes,
            line_color=line_color,
            fill_color=fill_color,
            fill_alpha=fill_alpha,
            legend_label=f"{session} trading session",
        )

    def _plot_trade(
        self,
        x_data,
        y_data,
        marker_type,
        marker_colour,
        label,
        linked_fig,
        scatter_size=15,
    ):
        """Plots individual trade."""

        linked_fig.scatter(
            x_data,
            y_data,
            marker=marker_type,
            size=scatter_size,
            fill_color=marker_colour,
            legend_label=label,
        )

    def _plot_trade_history(
        self,
        trade_summary: pd.DataFrame,
        linked_fig,
        order_summary: pd.DataFrame = None,
        cancelled_summary: bool = False,
        open_summary: bool = False,
    ):
        """Plots trades taken over an ohlc chart."""
        if order_summary is not None:
            # Merge order summary based on trade fill times
            merged_os = pd.merge(
                order_summary, trade_summary, left_on="order_id", right_on="order_id"
            )
            sl_tp = merged_os[["stop_loss", "take_profit", "fill_time"]]

        if self._backtest_data is not None:
            # Charting on different timeframe data
            trade_summary = pd.merge(
                self._backtest_data, trade_summary, left_index=True, right_index=True
            )
            if order_summary is not None:
                sl_tp = pd.merge(
                    self._backtest_data, sl_tp, left_index=True, right_on="fill_time"
                )
        else:
            # Charting on same timeframe data
            trade_summary = pd.merge(
                self._data, trade_summary, left_on="date", right_index=True
            )
            if order_summary is not None:
                sl_tp = pd.merge(
                    self._data, sl_tp, left_on="date", right_on="fill_time"
                )

        # Backtesting signals
        long_trades = trade_summary[trade_summary["direction"] > 0]
        shorts_trades = trade_summary[trade_summary["direction"] < 0]

        if cancelled_summary is False and open_summary is False:
            # Long trades
            if len(long_trades) > 0:
                self._plot_trade(
                    list(long_trades.data_index.values),
                    list(long_trades.fill_price.values),
                    "triangle",
                    "lightgreen",
                    "Long trades",
                    linked_fig,
                )

            # Short trades
            if len(shorts_trades) > 0:
                self._plot_trade(
                    list(shorts_trades.data_index.values),
                    list(shorts_trades.fill_price.values),
                    "inverted_triangle",
                    "orangered",
                    "Short trades",
                    linked_fig,
                )

        else:
            if cancelled_summary:
                long_legend_label = "Cancelled long trades"
                short_legend_label = "Cancelled short trades"
                fill_color = "black"
                price = "order_price"
            else:
                long_legend_label = "Open long trades"
                short_legend_label = "Open short trades"
                fill_color = "white"
                price = "fill_price"

            # Partial long trades
            if len(long_trades) > 0:
                linked_fig.scatter(
                    list(long_trades.data_index.values),
                    list(long_trades[price].values),
                    marker="triangle",
                    size=15,
                    fill_color=fill_color,
                    legend_label=long_legend_label,
                    visible=False,  # hide by default
                )

            # Partial short trades
            if len(shorts_trades) > 0:
                linked_fig.scatter(
                    list(shorts_trades.data_index.values),
                    list(shorts_trades[price].values),
                    marker="inverted_triangle",
                    size=15,
                    fill_color=fill_color,
                    legend_label=short_legend_label,
                    visible=False,  # hide by default
                )

        # Stop loss levels
        if order_summary is not None:
            if None not in sl_tp["stop_loss"].values:
                self._plot_trade(
                    list(sl_tp.data_index.values),
                    list(sl_tp["stop_loss"].fillna("").values),
                    "dash",
                    "black",
                    "Stop loss",
                    linked_fig,
                )

            # Take profit levels
            if None not in sl_tp["take_profit"].values:
                self._plot_trade(
                    list(sl_tp.data_index.values),
                    list(sl_tp["take_profit"].fillna("").values),
                    "dash",
                    "black",
                    "Take profit",
                    linked_fig,
                )

    def _plot_macd(self, x_range, macd_data, linked_fig):
        """Plots MACD indicator."""
        # Initialise figure
        fig = figure(
            width=linked_fig.width,
            height=self._bottom_fig_height,
            title=None,
            tools=linked_fig.tools,
            active_drag=linked_fig.tools[0],
            active_scroll=linked_fig.tools[1],
            x_range=linked_fig.x_range,
        )

        # Add glyphs
        source = ColumnDataSource(self._data)
        for key, item in macd_data.items():
            if key == "type":
                pass
            else:
                merged_data = self._merge_data(item)[item.name]
                source.add(merged_data, key)

        fig.line("data_index", "macd", source=source, line_color="blue")
        fig.line("data_index", "signal", source=source, line_color="red")
        if "histogram" in macd_data:
            histcolour = []
            for i in range(len(macd_data["histogram"])):
                if np.isnan(macd_data["histogram"].iloc[i]):
                    histcolour.append("lightblue")
                else:
                    if macd_data["histogram"].iloc[i] < 0:
                        histcolour.append("red")
                    else:
                        histcolour.append("lightblue")

            fig.quad(
                top=macd_data["histogram"],
                bottom=0,
                left=x_range - 0.3,
                right=x_range + 0.3,
                fill_color=histcolour,
            )

        if "crossvals" in macd_data:
            fig.scatter(
                x_range,
                macd_data["crossvals"],
                marker="dash",
                size=15,
                fill_color="black",
                legend_label="Last Crossover Value",
            )

        # Define autoscale arguments
        source.add(np.maximum(macd_data["macd"], macd_data["signal"]), "High")
        source.add(np.minimum(macd_data["macd"], macd_data["signal"]), "Low")
        self._add_to_autoscale_args(source, fig.y_range)

        return fig

    def _plot_bars(
        self,
        x_vals,
        data_name,
        source,
        linked_fig=None,
        fig_height=250,
        fig_title=None,
        hover_name=None,
    ):
        x_range = x_vals if linked_fig is None else linked_fig.x_range
        tooltips = f"@index: @{hover_name}" if linked_fig is None else f"@{hover_name}"
        fig = figure(
            x_range=x_range,
            title=fig_title,
            toolbar_location=None,
            tools=self._fig_tools + ",ywheel_zoom",
            tooltips=tooltips,
            height=fig_height,
            active_drag="pan",
            active_scroll="wheel_zoom",
        )

        fig.vbar(x="index", top=data_name, width=0.9, color="color", source=source)

        if linked_fig is not None:
            # Plotting indicator, define autoscale arguments
            source.add(source.data["plot_data"], "High")
            source.add(np.zeros(len(source.data["plot_data"])), "Low")
            self._add_to_autoscale_args(source, fig.y_range)

        return fig

    def _plot_pie(self, source, fig_title=None, fig_height=250):
        pie = figure(
            title=fig_title,
            toolbar_location=None,
            tools="hover",
            tooltips="@index: @trades trades",
            x_range=(-1, 1),
            y_range=(0.0, 2.0),
            height=fig_height,
        )

        pie.wedge(
            x=0,
            y=1,
            radius=0.2,
            start_angle=cumsum("angle", include_zero=True),
            end_angle=cumsum("angle"),
            line_color="white",
            fill_color="color",
            legend_field="index",
            source=source,
        )

        return pie

    def _plot_bands(
        self,
        plot_data,
        linked_fig=None,
        new_fig=True,
        fill_color="blue",
        fill_alpha=0.3,
        line_color="black",
        legend_label=None,
    ):
        """Plots a shaded region bound by upper and lower vaues.

        lower, upper and mid data must have same length as self._data.

        Parameters:
            plot_data (dict): a dictionary containing keys 'lower', 'upper',
            corresponding to the lower and upper bounding values (which may be
            an integer or timeseries). Optional keys include:
                - band_name: legend name for bands
                - fill_color: color filling upper and lower bands
                - fill_alpha: transparency of fill (0 - 1)
                - mid: data for a mid line
                - mid_name: legend name for mid line
                - line_color: line color for mid line

            linked_fig (Bokeh figure): linked figure

            new_fig (bool): flag to return a new figure or overlay on linked_fig
        """

        fill_color = (
            plot_data["fill_color"] if "fill_color" in plot_data else fill_color
        )
        fill_alpha = (
            plot_data["fill_alpha"] if "fill_alpha" in plot_data else fill_alpha
        )
        line_color = (
            plot_data["line_color"] if "line_color" in plot_data else line_color
        )

        if new_fig:
            # Plot on new fig
            fig = figure(
                width=linked_fig.width,
                height=self._bottom_fig_height,
                title=None,
                tools=linked_fig.tools,
                active_drag=linked_fig.tools[0],
                active_scroll=linked_fig.tools[1],
                x_range=linked_fig.x_range,
            )

        else:
            # Plot over linked figure
            fig = linked_fig

        # Charting on different timeframe data
        lower_band = self._merge_data(plot_data["lower"], name="lower")["lower"]
        upper_band = self._merge_data(plot_data["upper"], name="upper")["upper"]

        fig.varea(
            lower_band.index,
            lower_band.values,
            upper_band.values,
            fill_alpha=fill_alpha,
            fill_color=fill_color,
            legend_label=(
                plot_data["band_name"] if "band_name" in plot_data else legend_label
            ),
        )

        if "mid" in plot_data:
            # Add a mid line
            mid_line = self._merge_data(plot_data["mid"], name="mid")["mid"]
            fig.line(
                mid_line.index,
                mid_line.values,
                line_color=line_color,
                legend_label=(
                    plot_data["mid_name"]
                    if "mid_name" in plot_data
                    else "Band Mid Line"
                ),
            )

        return fig
