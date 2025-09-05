import reflex as rx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
from typing import Literal
import uuid
from pydantic import BaseModel
import json
from app.states.slice_state import SliceState, Slice, PlotConfig


class DataState(rx.State):
    """Manages the application's data and UI state."""

    uploaded_filename: str = rx.LocalStorage("", name="dataviz_filename")
    data: pd.DataFrame = pd.DataFrame()
    data_columns: list[str] = []
    is_loading: bool = False
    upload_message: str = "Upload a CSV file to begin."
    grid_columns: int = 2
    show_add_chart_modal: bool = False
    show_upload_page: bool = False
    categorical_vars: list[str] = [
        "VariableGroup",
        "Subgroup",
        "Variable",
        "Area",
        "Unit",
        "Symbol",
    ]
    numerical_vars: list[str] = ["Year", "Value"]
    x_axis_options: list[str] = ["Year", "Area"]
    variable_groups: list[str] = []
    editing_plot_id: str = ""

    @rx.event
    def toggle_upload_page(self):
        self.show_upload_page = not self.show_upload_page

    @rx.event
    def toggle_add_chart_modal(self):
        self.show_add_chart_modal = not self.show_add_chart_modal

    @rx.event
    def set_grid_columns(self, cols: int):
        self.grid_columns = cols
        yield rx.call_script("window.dispatchEvent(new Event('resize'))")

    @rx.event
    async def reset_data(self):
        self.data = pd.DataFrame()
        self.data_columns = []
        slice_state = await self.get_state(SliceState)
        slice_state.slices_json = "[]"
        slice_state.create_new_slice()
        self.variable_groups = []
        self.uploaded_filename = ""
        self.upload_message = "Upload a CSV file to begin."

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handles the CSV file upload and processing."""
        if not files:
            self.upload_message = "No file selected."
            return
        self.is_loading = True
        self.upload_message = "Processing file..."
        yield
        try:
            file = files[0]
            token = self.router.session.client_token
            new_filename = f"{token}_{file.name}"
            file_path = rx.get_upload_dir() / new_filename
            with file_path.open("wb") as f:
                data = await file.read()
                f.write(data)
            df = pd.read_csv(file_path)
            df.columns = [col.strip() for col in df.columns]
            self.data = df
            self.data_columns = df.columns.tolist()
            slice_state = await self.get_state(SliceState)
            slice_state.slices_json = "[]"
            slice_state.create_new_slice()
            self.variable_groups = ["All"] + df["VariableGroup"].unique().tolist()
            self.upload_message = f"Successfully uploaded {file.name}."
            self.uploaded_filename = new_filename
            self.show_upload_page = False
        except Exception as e:
            logging.exception(f"Error processing file: {e}")
            self.upload_message = f"Error processing file: {e}"
        finally:
            self.is_loading = False

    @rx.event
    async def load_data_from_storage(self):
        """Loads data from the filename stored in local storage."""
        if not self.uploaded_filename:
            return
        self.is_loading = True
        self.upload_message = f"Loading {self.uploaded_filename}..."
        yield
        try:
            file_path = rx.get_upload_dir() / self.uploaded_filename
            if not file_path.exists():
                raise FileNotFoundError(
                    f"File {self.uploaded_filename} not found on server."
                )
            df = pd.read_csv(file_path)
            df.columns = [col.strip() for col in df.columns]
            self.data = df
            self.data_columns = df.columns.tolist()
            self.variable_groups = ["All"] + df["VariableGroup"].unique().tolist()
            self.upload_message = f"Successfully loaded {self.uploaded_filename}."
            slice_state = await self.get_state(SliceState)
            slices = slice_state.slices
            if not slice_state.active_slice_id and slices:
                slice_state.active_slice_id = slices[0].id
            elif not slices:
                slice_state.create_new_slice()
        except Exception as e:
            logging.exception(f"Error loading stored file: {e}")
            self.upload_message = (
                "Could not load previous dataset. Please upload a new file."
            )
            self.uploaded_filename = ""
        finally:
            self.is_loading = False

    @rx.var
    def subgroups(self) -> list[str]:
        from app.states.plot_state import PlotState

        "Get unique subgroups based on selected variable group."
        if self.data.empty:
            return ["All"]
        df = self.data.copy()
        if (
            self.router.page.params.get(
                f"{PlotState.get_name()}.new_plot_variable_group"
            )
            and self.router.page.params.get(
                f"{PlotState.get_name()}.new_plot_variable_group"
            )
            != "All"
        ):
            df = df[
                df["VariableGroup"]
                == self.router.page.params.get(
                    f"{PlotState.get_name()}.new_plot_variable_group"
                )
            ]
        return ["All"] + df["Subgroup"].unique().tolist()

    @rx.var
    def variables(self) -> list[str]:
        from app.states.plot_state import PlotState

        "Get unique variables based on selected group and subgroup."
        if self.data.empty:
            return ["All"]
        df = self.data.copy()
        if (
            self.router.page.params.get(
                f"{PlotState.get_name()}.new_plot_variable_group"
            )
            and self.router.page.params.get(
                f"{PlotState.get_name()}.new_plot_variable_group"
            )
            != "All"
        ):
            df = df[
                df["VariableGroup"]
                == self.router.page.params.get(
                    f"{PlotState.get_name()}.new_plot_variable_group"
                )
            ]
        if (
            self.router.page.params.get(f"{PlotState.get_name()}.new_plot_subgroup")
            and self.router.page.params.get(f"{PlotState.get_name()}.new_plot_subgroup")
            != "All"
        ):
            df = df[
                df["Subgroup"]
                == self.router.page.params.get(
                    f"{PlotState.get_name()}.new_plot_subgroup"
                )
            ]
        return ["All"] + df["Variable"].unique().tolist()

    @rx.event
    async def remove_plot(self, plot_id: str):
        """Removes a plot from the list by its ID."""
        slice_state = await self.get_state(SliceState)
        all_slices = slice_state.slices
        for s in all_slices:
            if s.id == slice_state.active_slice_id:
                s.plots = [p for p in s.plots if p.id != plot_id]
                break
        slice_state.slices_json = json.dumps([s.model_dump() for s in all_slices])

    @rx.var
    async def plot_figures(self) -> list[go.Figure]:
        """Generates a list of Plotly figures for all configured plots."""
        slice_state = await self.get_state(SliceState)
        plots = slice_state.plots
        figs = []
        if self.data.empty:
            return figs
        for config_model in plots:
            config = config_model.model_dump()
            if config["plot_type"] == "invalid":
                fig = go.Figure()
                fig.add_annotation(
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    text="Invalid Plot",
                    showarrow=False,
                    font=dict(size=20, color="red"),
                )
                figs.append(fig)
                continue
            df_filtered = self.data.copy()
            if config["variable_group"] != "All":
                df_filtered = df_filtered[
                    df_filtered["VariableGroup"] == config["variable_group"]
                ]
            if config["subgroup"] != "All":
                df_filtered = df_filtered[df_filtered["Subgroup"] == config["subgroup"]]
            if config["variable"] != "All":
                df_filtered = df_filtered[df_filtered["Variable"] == config["variable"]]
            x, y, plot_type, series_by, series_values = (
                config["x_axis"],
                config["y_axis"],
                config["plot_type"],
                config["series_by"],
                config["series_values"],
            )
            color = series_by if series_values else None
            if series_by and series_values:
                df_filtered = df_filtered[df_filtered[series_by].isin(series_values)]
            if (
                df_filtered.empty
                or x not in df_filtered.columns
                or y not in df_filtered.columns
            ):
                figs.append(go.Figure())
                continue
            hover_cols = [
                col for col in ["Year", "Area", "Unit"] if col in df_filtered.columns
            ]
            cols_to_keep = list(set([x, y] + hover_cols + ([color] if color else [])))
            df_sample = df_filtered[cols_to_keep].dropna(subset=[x, y])
            if len(df_sample) > 500:
                df_sample = df_sample.sample(n=500, random_state=42)
            fig = None
            try:
                if plot_type == "scatter":
                    fig = px.scatter(
                        df_sample, x=x, y=y, color=color, hover_data=hover_cols
                    )
                elif plot_type == "line":
                    fig = px.line(
                        df_sample.sort_values(by=x),
                        x=x,
                        y=y,
                        color=color,
                        hover_data=hover_cols,
                    )
                elif plot_type in ("stacked bar", "multi bar"):
                    group_cols = [x]
                    if color:
                        group_cols.append(color)
                    agg_spec = {y: "mean"}
                    for col in hover_cols:
                        if col not in group_cols:
                            agg_spec[col] = "first"
                    df_agg = df_sample.groupby(group_cols, as_index=False).agg(agg_spec)
                    barmode = "group" if plot_type == "multi bar" else "stack"
                    fig = px.bar(
                        df_agg,
                        x=x,
                        y=y,
                        color=color,
                        barmode=barmode,
                        hover_data=hover_cols,
                    )
            except Exception as e:
                logging.exception(f"Error creating plot: {e}")
                fig = go.Figure()
            if fig:
                unit = ""
                if "Unit" in df_filtered.columns:
                    unit_series = df_filtered[df_filtered[y].notna()]["Unit"]
                    if not unit_series.empty:
                        unit = unit_series.iloc[0]
                y_axis_title = unit if unit else y.replace("_", " ").title()
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#6B7280", "family": "Inter"},
                    xaxis={"gridcolor": "#E5E7EB"},
                    yaxis={"gridcolor": "#E5E7EB", "title": y_axis_title},
                    margin=dict(l=20, r=20, t=20, b=20),
                )
            else:
                fig = go.Figure()
            figs.append(fig)
        return figs

    @rx.var
    async def plots_with_figures(self) -> list[dict]:
        """Pairs plot configs with titles for the UI."""
        slice_state = await self.get_state(SliceState)
        plots = slice_state.plots
        if not plots:
            return []
        plots_with_figs = []
        for i, config_model in enumerate(plots):
            config = config_model.model_dump()
            y_title = config["y_axis"].replace("_", " ").title()
            x_title = config["x_axis"].replace("_", " ").title()
            main_subject = y_title
            filter_parts = []
            if config["variable_group"] != "All":
                filter_parts.append(config["variable_group"])
            if config["subgroup"] != "All":
                filter_parts.append(config["subgroup"])
            if config["variable"] != "All":
                filter_parts.append(config["variable"])
            if filter_parts:
                main_subject = ", ".join(filter_parts)
            title = f"{main_subject} vs. {x_title}"
            if config["series_by"]:
                title += f" by {config['series_by']}"
            plot_info = {**config, "title": title}
            plots_with_figs.append(plot_info)
        return plots_with_figs

    @rx.event
    def set_show_add_chart_modal(self, open: bool):
        from app.states.plot_state import PlotState

        self.show_add_chart_modal = open
        if not open:
            return PlotState.cancel_editing