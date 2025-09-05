import reflex as rx
from app.states.data_state import DataState
from app.states.plot_state import PlotState
from app.states.slice_state import SliceState


def plot_card(plot: dict, index: int) -> rx.Component:
    """A card that displays a single plot and a remove button."""
    return rx.el.div(
        rx.el.div(
            rx.el.h3(plot["title"], class_name="text-lg font-semibold text-gray-700"),
            rx.el.div(
                rx.el.button(
                    rx.icon(tag="pencil", class_name="w-4 h-4"),
                    on_click=lambda: PlotState.start_editing_plot(plot["id"]),
                    class_name="p-1 rounded-full text-gray-500 hover:bg-gray-200",
                    aria_label="Edit plot",
                ),
                rx.el.button(
                    rx.icon(tag="x", class_name="w-4 h-4"),
                    on_click=lambda: DataState.remove_plot(plot["id"]),
                    class_name="p-1 rounded-full text-gray-500 hover:bg-gray-200",
                    aria_label="Remove plot",
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="flex justify-between items-center mb-2",
        ),
        rx.el.div(
            rx.cond(
                plot["plot_type"] == "invalid",
                rx.el.div(
                    rx.icon(tag="circle_x", class_name="w-12 h-12 text-red-500"),
                    rx.el.p(
                        "Invalid plot configuration", class_name="text-red-500 mt-2"
                    ),
                    class_name="flex flex-col items-center justify-center w-full h-full",
                ),
                rx.plotly(
                    data=DataState.plot_figures[index],
                    use_resize_handler=True,
                    style={"width": "100%", "height": "100%"},
                ),
            ),
            class_name="w-full h-[400px]",
        ),
        class_name="w-full bg-white rounded-xl shadow-sm border border-gray-200 p-4",
    )


def plots_area() -> rx.Component:
    """An area to display generated plots."""
    return rx.cond(
        SliceState.plots.length() > 0,
        rx.el.div(
            rx.foreach(DataState.plots_with_figures, plot_card),
            class_name=rx.match(
                DataState.grid_columns,
                (1, "grid grid-cols-1 gap-8 w-full"),
                (2, "grid grid-cols-1 md:grid-cols-2 gap-8 w-full"),
                "grid grid-cols-1 md:grid-cols-2 gap-8 w-full",
            ),
        ),
        rx.el.div(
            rx.icon(tag="pie-chart", class_name="w-16 h-16 text-gray-300 mb-4"),
            rx.el.h3(
                "No Plots to Display", class_name="text-xl font-semibold text-gray-500"
            ),
            rx.el.p(
                "Click the '+' button to add a new plot.", class_name="text-gray-400"
            ),
            class_name="flex flex-col items-center justify-center w-full min-h-[60vh] bg-white rounded-xl border-2 border-dashed border-gray-200",
        ),
    )