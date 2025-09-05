import reflex as rx
import pandas as pd
import logging
import uuid
from typing import Literal
import json
from app.states.data_state import DataState
from app.states.slice_state import SliceState, PlotConfig


class PlotState(rx.State):
    """Manages the state for creating and editing plots."""

    new_plot_type: str = "scatter"
    new_plot_x_axis: str = "Year"
    new_plot_variable_group: str = "All"
    new_plot_subgroup: str = "All"
    new_plot_variable: str = "All"
    new_plot_series_values: list[str] = []
    series_top_n: str = ""
    series_filter_text: str = ""
    editing_plot_id: str = ""

    @rx.var
    def series_by(self) -> str:
        if self.new_plot_x_axis == "Year":
            return "Area"
        if self.new_plot_x_axis == "Area":
            return "Year"
        return ""

    async def _get_filtered_data_for_controls(self) -> pd.DataFrame:
        data_state = await self.get_state(DataState)
        if data_state.data.empty:
            return pd.DataFrame()
        df = data_state.data.copy()
        if self.new_plot_variable_group != "All":
            df = df[df["VariableGroup"] == self.new_plot_variable_group]
        if self.new_plot_subgroup != "All":
            df = df[df["Subgroup"] == self.new_plot_subgroup]
        if self.new_plot_variable != "All":
            df = df[df["Variable"] == self.new_plot_variable]
        return df

    @rx.var
    async def series_options(self) -> list[str]:
        if not self.series_by:
            return []
        df = await self._get_filtered_data_for_controls()
        if df.empty:
            return []
        sorted_options = []
        if self.series_by == "Area" and "Value" in df.columns:
            avg_values = df.groupby("Area")["Value"].mean().sort_values(ascending=False)
            sorted_options = avg_values.index.tolist()
        elif self.series_by in df.columns:
            unique_values = df[self.series_by].unique()
            try:
                sorted_numeric = sorted(unique_values, key=float, reverse=True)
                return [str(v) for v in sorted_numeric]
            except (ValueError, TypeError) as e:
                logging.exception(f"Error sorting series options: {e}")
                sorted_alpha = sorted(unique_values)
                return [str(v) for v in sorted_alpha]
        return [str(opt) for opt in sorted_options]

    @rx.var
    async def filtered_series_options(self) -> list[str]:
        """Filters series options based on filter text."""
        options = await self.series_options
        if self.series_filter_text.strip() == "":
            return options
        return [
            opt
            for opt in options
            if self.series_filter_text.lower() in str(opt).lower()
        ]

    @rx.event
    def set_new_plot_variable_group(self, value: str):
        self.new_plot_variable_group = value
        self.new_plot_subgroup = "All"
        self.new_plot_variable = "All"

    @rx.event
    def set_new_plot_subgroup(self, value: str):
        self.new_plot_subgroup = value
        self.new_plot_variable = "All"

    @rx.event
    async def set_new_plot_variable(self, value: str):
        self.new_plot_variable = value
        yield
        current_top_n = self.series_top_n
        if current_top_n:
            self.series_top_n = ""
            yield PlotState.set_series_top_n(current_top_n)

    @rx.event
    def set_new_plot_type(self, value: str):
        self.new_plot_type = value

    @rx.event
    def set_new_plot_x_axis(self, value: str):
        self.new_plot_x_axis = value
        self.new_plot_series_values = []

    @rx.event
    def toggle_series_value(self, value: str):
        if value in self.new_plot_series_values:
            self.new_plot_series_values.remove(value)
        else:
            self.new_plot_series_values.append(value)

    @rx.event
    def clear_series_filter_text(self):
        self.series_filter_text = ""

    @rx.event
    async def cancel_editing(self):
        if self.editing_plot_id:
            self.editing_plot_id = ""
            await self._reset_new_plot_fields()

    async def _reset_new_plot_fields(self):
        from app.states.data_state import DataState

        data_state = await self.get_state(DataState)
        x_axis_options = data_state.x_axis_options
        self.new_plot_type = "scatter"
        self.new_plot_x_axis = x_axis_options[0] if x_axis_options else "Year"
        self.new_plot_variable_group = "All"
        self.new_plot_subgroup = "All"
        self.new_plot_variable = "All"
        self.new_plot_series_values = []
        self.series_top_n = ""
        self.series_filter_text = ""

    @rx.event
    async def set_series_top_n(self, value: str):
        self.series_top_n = value
        if not self.series_by:
            self.new_plot_series_values = []
            return
        df = await self._get_filtered_data_for_controls()
        if df.empty:
            self.new_plot_series_values = []
            return
        sorted_options = []
        if self.series_by == "Area" and "Value" in df.columns:
            avg_values = df.groupby("Area")["Value"].mean().sort_values(ascending=False)
            sorted_options = [str(opt) for opt in avg_values.index.tolist()]
        elif self.series_by in df.columns:
            unique_values = df[self.series_by].unique()
            try:
                sorted_options = [
                    str(v) for v in sorted(unique_values, key=float, reverse=True)
                ]
            except (ValueError, TypeError) as e:
                logging.exception(f"Error sorting series options: {e}")
                sorted_options = [str(v) for v in sorted(unique_values)]
        if value == "None" or value == "":
            self.new_plot_series_values = []
        elif value == "All":
            self.new_plot_series_values = sorted_options
        else:
            try:
                n = int(value)
                self.new_plot_series_values = sorted_options[:n]
            except (ValueError, TypeError) as e:
                logging.exception(f"Error converting top_n to int: {e}")
                self.new_plot_series_values = []

    @rx.event
    async def start_editing_plot(self, plot_id: str):
        from app.states.data_state import DataState

        self.editing_plot_id = plot_id
        data_state = await self.get_state(DataState)
        slice_state = await self.get_state(SliceState)
        plot_to_edit = None
        for p in slice_state.plots:
            if p.id == plot_id:
                plot_to_edit = p
                break
        if plot_to_edit:
            self.new_plot_type = plot_to_edit.plot_type
            self.new_plot_x_axis = plot_to_edit.x_axis
            self.new_plot_variable_group = plot_to_edit.variable_group
            self.new_plot_subgroup = plot_to_edit.subgroup
            self.new_plot_variable = plot_to_edit.variable
            self.new_plot_series_values = plot_to_edit.series_values
            self.series_top_n = ""
            self.series_filter_text = ""
            data_state.show_add_chart_modal = True

    @rx.event
    async def save_plot(self):
        from app.states.data_state import DataState

        data_state = await self.get_state(DataState)
        slice_state = await self.get_state(SliceState)
        plot_data = {
            "plot_type": self.new_plot_type,
            "x_axis": self.new_plot_x_axis,
            "y_axis": "Value",
            "variable_group": self.new_plot_variable_group,
            "subgroup": self.new_plot_subgroup,
            "variable": self.new_plot_variable,
            "series_by": self.series_by,
            "series_values": self.new_plot_series_values,
        }
        all_slices = slice_state.slices
        for s in all_slices:
            if s.id == slice_state.active_slice_id:
                if self.editing_plot_id:
                    for i, p in enumerate(s.plots):
                        if p.id == self.editing_plot_id:
                            updated_plot = PlotConfig(
                                id=self.editing_plot_id, **plot_data
                            )
                            s.plots[i] = updated_plot
                            break
                else:
                    new_plot = PlotConfig(id=str(uuid.uuid4()), **plot_data)
                    s.plots.append(new_plot)
                break
        slice_state.slices_json = json.dumps([s.model_dump() for s in all_slices])
        data_state.show_add_chart_modal = False
        self.editing_plot_id = ""
        await self._reset_new_plot_fields()