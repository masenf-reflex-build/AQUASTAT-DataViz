import reflex as rx
from app.components.charts import plots_area
from app.components.header import header
from app.components.controls import upload_page
from app.components.modals import add_chart_modal, export_modal, import_modal
from app.states.data_state import DataState


def dashboard() -> rx.Component:
    """The main dashboard view, shown after data is uploaded."""
    return rx.el.div(
        header(),
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Water Scarcity & Human Development Analysis",
                    class_name="text-3xl font-bold text-gray-800 mb-2",
                ),
                rx.el.p(
                    "Visualize relationships between development indicators and water-related issues.",
                    class_name="text-gray-500",
                ),
                class_name="mb-8",
            ),
            plots_area(),
            class_name="flex-1 p-8 md:p-12",
        ),
        add_chart_modal(),
        export_modal(),
        import_modal(),
        class_name="w-full bg-gray-50 min-h-screen",
    )


def index() -> rx.Component:
    """The main page of the application."""
    return rx.el.main(
        rx.cond(
            rx.State.is_hydrated,
            rx.cond(
                (DataState.data_columns.length() > 0) & ~DataState.show_upload_page,
                dashboard(),
                upload_page(),
            ),
            rx.el.div(
                rx.icon(
                    tag="loader", class_name="h-16 w-16 animate-spin text-blue-600"
                ),
                class_name="flex items-center justify-center min-h-screen",
            ),
        ),
        on_mount=DataState.load_data_from_storage,
        class_name="font-['Inter'] bg-gray-100",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)