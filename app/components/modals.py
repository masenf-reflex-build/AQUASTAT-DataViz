import reflex as rx
from app.states.data_state import DataState
from app.states.plot_state import PlotState
from app.states.slice_state import SliceState
from app.components.controls import axis_variable_controls, series_multiselect


def add_chart_modal() -> rx.Component:
    """A modal for adding a new chart."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.el.button(
                rx.icon(tag="plus", class_name="w-6 h-6"),
                class_name="fixed bottom-8 right-8 p-4 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 z-20",
            )
        ),
        rx.dialog.content(
            rx.el.div(
                rx.el.div(
                    rx.dialog.title(
                        rx.cond(
                            PlotState.editing_plot_id != "",
                            "Edit Plot",
                            "Create a New Plot",
                        ),
                        class_name="text-lg font-semibold text-gray-800",
                    ),
                    rx.dialog.close(
                        rx.el.button(
                            rx.icon(tag="x", class_name="w-4 h-4"),
                            class_name="p-1 rounded-full hover:bg-gray-200",
                        )
                    ),
                    class_name="flex justify-between items-center mb-1",
                ),
                rx.dialog.description(
                    rx.cond(
                        PlotState.editing_plot_id != "",
                        "Modify the properties of your existing plot.",
                        "Configure the properties of your new plot.",
                    ),
                    class_name="text-sm text-gray-500 mb-4",
                ),
                rx.scroll_area(
                    rx.el.div(
                        axis_variable_controls(),
                        rx.cond(
                            PlotState.series_by != "",
                            series_multiselect(),
                            rx.el.div(
                                rx.icon(
                                    tag="list-tree",
                                    class_name="w-12 h-12 text-gray-300",
                                ),
                                rx.el.p(
                                    "Select X-Axis to configure series",
                                    class_name="text-gray-400 text-sm mt-2 text-center",
                                ),
                                class_name="flex flex-col items-center justify-center h-full p-4 border-2 border-dashed rounded-lg bg-gray-50",
                            ),
                        ),
                        class_name="grid grid-cols-1 lg:grid-cols-2 gap-6",
                    ),
                    type="auto",
                    scrollbars="vertical",
                    class_name="h-[50vh] pr-2",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.cond(
                            PlotState.editing_plot_id != "", "Update Plot", "Add Plot"
                        ),
                        on_click=PlotState.save_plot,
                        class_name="w-full px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors",
                    ),
                    class_name="pt-4 mt-4 border-t border-gray-200 flex-shrink-0",
                ),
                class_name="flex flex-col h-full",
            ),
            style={
                "max_width": "800px",
                "width": "90%",
                "max_height": "85vh",
                "border_radius": "12px",
                "padding": "24px",
            },
        ),
        open=DataState.show_add_chart_modal,
        on_open_change=DataState.set_show_add_chart_modal,
    )


def export_modal() -> rx.Component:
    """A modal to select slices for export."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                "Export Slices", class_name="text-lg font-semibold text-gray-800"
            ),
            rx.dialog.description(
                "Select the slices you want to download as a JSON file.",
                class_name="text-sm text-gray-500 mb-4",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.button(
                        "Select All",
                        on_click=SliceState.select_all_for_export,
                        variant="soft",
                        class_name="text-xs",
                    ),
                    rx.el.button(
                        "Select None",
                        on_click=SliceState.select_none_for_export,
                        variant="soft",
                        class_name="text-xs",
                    ),
                    class_name="flex gap-2 mb-3",
                ),
                rx.el.div(
                    rx.foreach(
                        SliceState.slices,
                        lambda slice_item: rx.el.label(
                            rx.el.input(
                                type="checkbox",
                                on_change=lambda: SliceState.toggle_slice_for_export(
                                    slice_item.id
                                ),
                                checked=SliceState.slices_to_export.contains(
                                    slice_item.id
                                ),
                                class_name="mr-2 rounded",
                            ),
                            slice_item.name,
                            class_name="flex items-center text-sm font-normal text-gray-600 p-2 rounded-md hover:bg-gray-100 cursor-pointer",
                        ),
                    ),
                    class_name="max-h-64 overflow-y-auto space-y-1 p-2 border rounded-md bg-gray-50",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.dialog.close(
                    rx.el.button(
                        "Cancel",
                        on_click=SliceState.toggle_export_modal,
                        variant="soft",
                        color_scheme="gray",
                    )
                ),
                rx.el.button(
                    "Download JSON", on_click=SliceState.export_selected_slices
                ),
                class_name="flex justify-end gap-3 mt-4",
            ),
            style={"max_width": "450px", "border_radius": "12px", "padding": "24px"},
        ),
        open=SliceState.show_export_modal,
        on_open_change=SliceState.set_show_export_modal,
    )


def import_modal() -> rx.Component:
    """A modal to import slices from a JSON file."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                "Import Slices", class_name="text-lg font-semibold text-gray-800"
            ),
            rx.dialog.description(
                "Upload a JSON file containing slices to import them into your workspace.",
                class_name="text-sm text-gray-500 mb-4",
            ),
            rx.cond(
                SliceState.parsed_slices.length() == 0,
                rx.upload.root(
                    rx.el.div(
                        rx.icon(
                            tag="cloud-upload",
                            class_name="w-10 h-10 text-gray-400 mb-2",
                        ),
                        rx.el.p(
                            "Drag & drop or click to upload a JSON file",
                            class_name="text-gray-500 text-sm",
                        ),
                        class_name="flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors",
                    ),
                    id="json_import",
                    accept={"application/json": [".json"]},
                    on_drop=SliceState.handle_import_upload(
                        rx.upload_files(upload_id="json_import")
                    ),
                    multiple=False,
                    class_name="w-full cursor-pointer mb-4",
                ),
                rx.fragment(),
            ),
            rx.cond(
                SliceState.parsed_slices.length() > 0,
                rx.el.div(
                    rx.el.h4("Slices Found", class_name="font-semibold mb-2"),
                    rx.el.div(
                        rx.el.button(
                            "Select All",
                            on_click=SliceState.select_all_for_import,
                            variant="soft",
                            class_name="text-xs",
                        ),
                        rx.el.button(
                            "Select None",
                            on_click=SliceState.select_none_for_import,
                            variant="soft",
                            class_name="text-xs",
                        ),
                        class_name="flex gap-2 mb-3",
                    ),
                    rx.el.div(
                        rx.foreach(
                            SliceState.parsed_slices,
                            lambda slice_item: rx.el.label(
                                rx.el.input(
                                    type="checkbox",
                                    on_change=lambda: SliceState.toggle_slice_for_import(
                                        slice_item.id
                                    ),
                                    checked=SliceState.slices_to_import.contains(
                                        slice_item.id
                                    ),
                                    class_name="mr-2 rounded",
                                ),
                                slice_item.name,
                                class_name="flex items-center text-sm font-normal text-gray-600 p-2 rounded-md hover:bg-gray-100 cursor-pointer",
                            ),
                        ),
                        class_name="max-h-48 overflow-y-auto space-y-1 p-2 border rounded-md bg-gray-50",
                    ),
                ),
                rx.el.p(
                    SliceState.import_message, class_name="text-sm text-center h-5 mt-2"
                ),
            ),
            rx.el.div(
                rx.dialog.close(
                    rx.el.button(
                        "Cancel",
                        on_click=SliceState.toggle_import_modal,
                        variant="soft",
                        color_scheme="gray",
                    )
                ),
                rx.el.button(
                    "Import Slices",
                    on_click=SliceState.import_selected_slices,
                    disabled=SliceState.slices_to_import.length() == 0,
                ),
                class_name="flex justify-end gap-3 mt-4",
            ),
            style={"max_width": "450px", "border_radius": "12px", "padding": "24px"},
        ),
        open=SliceState.show_import_modal,
        on_open_change=SliceState.set_show_import_modal,
    )