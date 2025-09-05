import reflex as rx
from app.states.data_state import DataState
from app.states.slice_state import SliceState


def _grid_control_button(icon: str, cols: int) -> rx.Component:
    """A button to set the grid column layout."""
    return rx.el.button(
        rx.icon(tag=icon, class_name="w-5 h-5"),
        on_click=lambda: DataState.set_grid_columns(cols),
        class_name=rx.cond(
            DataState.grid_columns == cols,
            "p-2 rounded-lg bg-blue-100 text-blue-600",
            "p-2 rounded-lg text-gray-500 hover:bg-gray-100",
        ),
    )


def header() -> rx.Component:
    """The header component for the main dashboard."""
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.icon(tag="bar-chart-2", class_name="h-8 w-8 text-blue-600"),
                rx.el.h2("DataViz", class_name="text-2xl font-bold text-gray-800"),
                class_name="flex items-center gap-3",
            ),
            rx.el.div(
                rx.cond(
                    SliceState.is_renaming_slice,
                    rx.el.input(
                        default_value=SliceState.active_slice.name,
                        on_change=SliceState.set_current_slice_name,
                        on_blur=SliceState.save_slice_name,
                        on_key_down=lambda key: rx.cond(
                            key == "Enter", SliceState.save_slice_name(), rx.noop()
                        ),
                        auto_focus=True,
                        class_name="p-2 border rounded-md",
                    ),
                    rx.el.select(
                        rx.foreach(
                            SliceState.slices,
                            lambda slice: rx.el.option(slice.name, value=slice.id),
                        ),
                        rx.el.option("[New Slice]", value="new"),
                        value=SliceState.active_slice_id,
                        on_change=SliceState.set_active_slice_id,
                        class_name="p-2 border rounded-md shadow-sm",
                    ),
                ),
                rx.el.button(
                    rx.icon(tag="pencil", class_name="w-4 h-4"),
                    on_click=SliceState.toggle_rename_slice,
                    class_name="p-2 rounded-lg text-gray-500 hover:bg-gray-100",
                ),
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(
                        rx.el.button(
                            rx.icon(tag="trash-2", class_name="w-4 h-4 text-red-500"),
                            class_name="p-2 rounded-lg hover:bg-red-100",
                            disabled=SliceState.slices.length() <= 1,
                        )
                    ),
                    rx.alert_dialog.content(
                        rx.alert_dialog.title("Delete Slice"),
                        rx.alert_dialog.description(
                            "Are you sure you want to delete the current slice? This action cannot be undone."
                        ),
                        rx.el.div(
                            rx.alert_dialog.cancel(
                                rx.el.button(
                                    "Cancel", variant="soft", color_scheme="gray"
                                )
                            ),
                            rx.alert_dialog.action(
                                rx.el.button(
                                    "Delete",
                                    on_click=SliceState.delete_active_slice,
                                    color_scheme="red",
                                )
                            ),
                            class_name="flex gap-3 mt-4 justify-end",
                        ),
                        style={"max_width": "400px"},
                    ),
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                _grid_control_button("layout-grid", 2),
                _grid_control_button("square", 1),
                class_name="flex items-center gap-2 p-1 bg-gray-100 rounded-xl",
            ),
            rx.el.div(
                rx.el.button(
                    rx.el.div(
                        rx.icon(tag="cloud-upload", class_name="w-4 h-4"),
                        "Import",
                        class_name="flex items-center gap-2",
                    ),
                    on_click=SliceState.toggle_import_modal,
                    class_name="px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50",
                ),
                rx.el.button(
                    rx.el.div(
                        rx.icon(tag="cloud-download", class_name="w-4 h-4"),
                        "Export",
                        class_name="flex items-center gap-2",
                    ),
                    on_click=SliceState.toggle_export_modal,
                    class_name="px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50",
                ),
                rx.el.button(
                    "Upload New Data",
                    on_click=DataState.toggle_upload_page,
                    class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50",
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="flex items-center justify-between w-full",
        ),
        class_name="sticky top-0 z-10 w-full p-4 bg-white/80 backdrop-blur-md border-b border-gray-200",
    )