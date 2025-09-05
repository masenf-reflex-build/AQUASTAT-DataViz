import reflex as rx
from app.states.data_state import DataState
from app.states.plot_state import PlotState


def upload_page() -> rx.Component:
    """A full-page component for file uploading."""
    return rx.el.div(
        rx.el.div(
            rx.icon(tag="bar-chart-2", class_name="h-10 w-10 text-blue-600"),
            rx.el.h1("DataViz", class_name="text-4xl font-bold text-gray-800"),
            class_name="flex items-center gap-4 mb-8",
        ),
        rx.el.div(
            rx.el.h3(
                "Upload Your Dataset",
                class_name="text-2xl font-semibold text-gray-800 mb-4",
            ),
            rx.upload.root(
                rx.el.div(
                    rx.icon(
                        tag="cloud-upload", class_name="w-12 h-12 text-gray-400 mb-3"
                    ),
                    rx.el.p(
                        "Drag & drop or click to upload a CSV file",
                        class_name="text-gray-500",
                    ),
                    class_name="flex flex-col items-center justify-center p-8 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors",
                ),
                id="csv_upload",
                accept={"text/csv": [".csv"]},
                multiple=False,
                class_name="w-full cursor-pointer",
            ),
            rx.el.div(
                rx.foreach(
                    rx.selected_files("csv_upload"),
                    lambda file: rx.el.div(
                        rx.icon(
                            tag="file-text", class_name="w-5 h-5 mr-2 text-gray-500"
                        ),
                        file,
                        class_name="flex items-center text-gray-700 p-3 bg-gray-100 rounded-lg",
                    ),
                ),
                class_name="mt-4 space-y-2",
            ),
            rx.el.button(
                rx.cond(
                    DataState.is_loading,
                    rx.el.span("Processing...", class_name="animate-pulse"),
                    "Upload & Process",
                ),
                on_click=DataState.handle_upload(
                    rx.upload_files(upload_id="csv_upload")
                ),
                class_name="w-full mt-6 px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400",
                disabled=DataState.is_loading,
            ),
            rx.cond(
                (DataState.data_columns.length() > 0) & DataState.show_upload_page,
                rx.el.button(
                    "Cancel",
                    on_click=DataState.toggle_upload_page,
                    class_name="w-full mt-2 px-4 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors",
                ),
                rx.fragment(),
            ),
            rx.el.p(
                DataState.upload_message,
                class_name="mt-3 text-sm text-gray-600 text-center h-5",
            ),
            class_name="p-8 bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-lg",
        ),
        class_name="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4",
    )


def _select_control(
    label: str, items: rx.Var[list[str]], on_change, value: rx.Var[str]
) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name="text-sm font-medium text-gray-700 mb-1"),
        rx.el.select(
            rx.foreach(items, lambda item: rx.el.option(item, value=item)),
            on_change=on_change,
            value=value,
            class_name="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
        ),
        class_name="mb-4",
    )


def series_multiselect() -> rx.Component:
    """A multi-select component for series."""
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                f"Series (by {PlotState.series_by})",
                class_name="text-sm font-medium text-gray-700 block",
            ),
            rx.el.select(
                rx.el.option("Select", value="", disabled=True),
                rx.foreach(
                    rx.Var.create(["None", "5", "10", "20", "All"]),
                    lambda n: rx.el.option(
                        rx.cond(
                            n == "All", "All", rx.cond(n == "None", "None", f"Top {n}")
                        ),
                        value=n,
                    ),
                ),
                on_change=PlotState.set_series_top_n,
                value=PlotState.series_top_n,
                placeholder="Select",
                class_name="p-1 text-xs border border-gray-300 rounded-md shadow-sm",
            ),
            class_name="flex justify-between items-center mb-2",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Filter series...",
                on_change=PlotState.set_series_filter_text,
                class_name="w-full p-1 text-xs border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                default_value=PlotState.series_filter_text,
                id="filter_series",
            ),
            rx.cond(
                PlotState.series_filter_text != "",
                rx.el.button(
                    rx.icon(tag="x", class_name="w-4 h-4"),
                    on_click=[
                        rx.set_value("filter_series", ""),
                        PlotState.clear_series_filter_text,
                        rx.set_focus("filter_series"),
                    ],
                    class_name="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:bg-gray-200 hover:text-gray-600",
                ),
            ),
            class_name="relative mb-2",
        ),
        rx.el.div(
            rx.foreach(
                PlotState.filtered_series_options,
                lambda option: rx.el.label(
                    rx.el.input(
                        type="checkbox",
                        on_change=lambda _: PlotState.toggle_series_value(option),
                        checked=PlotState.new_plot_series_values.contains(option),
                        class_name="mr-2 rounded",
                    ),
                    option,
                    class_name="flex items-center text-sm font-normal text-gray-600",
                ),
            ),
            class_name="max-h-48 overflow-y-auto space-y-1 p-2 border rounded-md bg-gray-50",
        ),
        class_name="mb-4",
    )


def axis_variable_controls() -> rx.Component:
    """Component for plot type, axis, and variable selection."""
    return rx.el.div(
        _select_control(
            "Plot Type",
            rx.Var.create(["scatter", "line", "stacked bar", "multi bar"]),
            PlotState.set_new_plot_type,
            PlotState.new_plot_type,
        ),
        _select_control(
            "X-Axis",
            DataState.x_axis_options,
            PlotState.set_new_plot_x_axis,
            PlotState.new_plot_x_axis,
        ),
        rx.el.details(
            rx.el.summary(
                "Filter by Group/Subgroup",
                class_name="cursor-pointer font-medium text-gray-700 py-2 px-2",
            ),
            rx.el.div(
                _select_control(
                    "Group",
                    DataState.variable_groups,
                    PlotState.set_new_plot_variable_group,
                    PlotState.new_plot_variable_group,
                ),
                _select_control(
                    "Subgroup",
                    DataState.subgroups,
                    PlotState.set_new_plot_subgroup,
                    PlotState.new_plot_subgroup,
                ),
                class_name="p-4 pt-2",
            ),
            class_name="mb-4 border border-gray-300 rounded-md",
        ),
        _select_control(
            "Y-Axis",
            DataState.variables,
            PlotState.set_new_plot_variable,
            PlotState.new_plot_variable,
        ),
        class_name="flex flex-col gap-2",
    )