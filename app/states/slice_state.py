import reflex as rx
import logging
import uuid
from pydantic import BaseModel
import json
from typing import Literal


class PlotConfig(BaseModel):
    id: str
    plot_type: Literal["scatter", "line", "stacked bar", "multi bar", "invalid"]
    x_axis: str
    y_axis: str
    variable_group: str
    subgroup: str
    variable: str
    series_by: str
    series_values: list[str]


class Slice(BaseModel):
    id: str
    name: str
    plots: list[PlotConfig] = []


class SliceState(rx.State):
    slices_json: str = rx.LocalStorage("[]", name="dataviz_slices")
    active_slice_id: str = rx.LocalStorage("", name="dataviz_active_slice_id")
    is_renaming_slice: bool = False
    current_slice_name: str = ""
    show_export_modal: bool = False
    slices_to_export: list[str] = []
    show_import_modal: bool = False
    parsed_slices: list[Slice] = []
    slices_to_import: list[str] = []
    import_message: str = ""

    @rx.var
    def slices(self) -> list[Slice]:
        if not self.slices_json:
            return []
        try:
            slices_data = json.loads(self.slices_json)
            validated_slices = []
            for s_data in slices_data:
                validated_plots = []
                if "plots" in s_data and isinstance(s_data["plots"], list):
                    for p_data in s_data["plots"]:
                        try:
                            validated_plots.append(PlotConfig.model_validate(p_data))
                        except Exception as e:
                            logging.exception(
                                f"Invalid plot config found: {p_data}. Error: {e}"
                            )
                            invalid_plot_data = {
                                "id": p_data.get("id", uuid.uuid4()),
                                "plot_type": "invalid",
                                "x_axis": p_data.get("x_axis", ""),
                                "y_axis": p_data.get("y_axis", ""),
                                "variable_group": p_data.get("variable_group", ""),
                                "subgroup": p_data.get("subgroup", ""),
                                "variable": p_data.get("variable", ""),
                                "series_by": p_data.get("series_by", ""),
                                "series_values": p_data.get("series_values", []),
                            }
                            validated_plots.append(
                                PlotConfig.model_validate(invalid_plot_data)
                            )
                s_data["plots"] = validated_plots
                validated_slices.append(Slice.model_validate(s_data))
            return validated_slices
        except (json.JSONDecodeError, TypeError) as e:
            logging.exception(f"Error decoding slices JSON: {e}")
            return []

    @rx.var
    def active_slice(self) -> Slice | None:
        if not self.active_slice_id:
            return None
        for s in self.slices:
            if s.id == self.active_slice_id:
                return s
        return None

    @rx.var
    def plots(self) -> list[PlotConfig]:
        if self.active_slice:
            return self.active_slice.plots
        return []

    @rx.event
    def create_new_slice(self):
        new_slice_id = str(uuid.uuid4())
        all_slices = self.slices
        new_slice = Slice(id=new_slice_id, name=f"Slice {len(all_slices) + 1}")
        all_slices.append(new_slice)
        self.slices_json = json.dumps([s.model_dump() for s in all_slices])
        self.active_slice_id = new_slice_id

    @rx.event
    def set_active_slice_id(self, slice_id: str):
        if slice_id == "new":
            return SliceState.create_new_slice
        else:
            self.active_slice_id = slice_id

    @rx.event
    def toggle_rename_slice(self):
        self.is_renaming_slice = not self.is_renaming_slice
        if self.is_renaming_slice and self.active_slice:
            self.current_slice_name = self.active_slice.name
        else:
            self.current_slice_name = ""

    @rx.event
    def set_current_slice_name(self, name: str):
        self.current_slice_name = name

    @rx.event
    def save_slice_name(self):
        if not self.current_slice_name.strip():
            self.is_renaming_slice = False
            return
        all_slices = self.slices
        for s in all_slices:
            if s.id == self.active_slice_id:
                s.name = self.current_slice_name
                break
        self.slices_json = json.dumps([s.model_dump() for s in all_slices])
        self.is_renaming_slice = False
        self.current_slice_name = ""

    def set_show_export_modal(self, open: bool):
        self.show_export_modal = open
        if open:
            self.slices_to_export = [s.id for s in self.slices]
        else:
            self.slices_to_export = []

    def set_show_import_modal(self, open: bool):
        self.show_import_modal = open
        if not open:
            self.parsed_slices = []
            self.slices_to_import = []
            self.import_message = ""

    @rx.event
    def toggle_export_modal(self):
        self.set_show_export_modal(not self.show_export_modal)

    @rx.event
    def toggle_slice_for_export(self, slice_id: str):
        if slice_id in self.slices_to_export:
            self.slices_to_export.remove(slice_id)
        else:
            self.slices_to_export.append(slice_id)

    @rx.event
    def select_all_for_export(self):
        self.slices_to_export = [s.id for s in self.slices]

    @rx.event
    def select_none_for_export(self):
        self.slices_to_export = []

    @rx.event
    def export_selected_slices(self):
        """Exports selected slices as a JSON file."""
        selected_slices_data = [
            s.model_dump() for s in self.slices if s.id in self.slices_to_export
        ]
        if not selected_slices_data:
            return rx.toast("No slices selected for export.")
        json_data = json.dumps(selected_slices_data, indent=2)
        self.show_export_modal = False
        return rx.download(
            data=json_data.encode("utf-8"), filename="dataviz_slices.json"
        )

    @rx.event
    def toggle_import_modal(self):
        self.set_show_import_modal(not self.show_import_modal)

    @rx.event
    async def handle_import_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.import_message = "No file selected."
            return
        self.import_message = "Processing file..."
        yield
        try:
            file_content = await files[0].read()
            slices_data = json.loads(file_content)
            if not isinstance(slices_data, list):
                raise ValueError("JSON file must contain a list of slices.")
            self.parsed_slices = [Slice.model_validate(s) for s in slices_data]
            self.slices_to_import = [s.id for s in self.parsed_slices]
            self.import_message = (
                f"Found {len(self.parsed_slices)} slices. Select which to import."
            )
        except Exception as e:
            logging.exception(f"Error parsing import file: {e}")
            self.import_message = f"Error: Could not parse file. {e}"
            self.parsed_slices = []
            self.slices_to_import = []

    @rx.event
    def toggle_slice_for_import(self, slice_id: str):
        if slice_id in self.slices_to_import:
            self.slices_to_import.remove(slice_id)
        else:
            self.slices_to_import.append(slice_id)

    @rx.event
    def select_all_for_import(self):
        self.slices_to_import = [s.id for s in self.parsed_slices]

    @rx.event
    def select_none_for_import(self):
        self.slices_to_import = []

    @rx.event
    def import_selected_slices(self):
        if not self.slices_to_import:
            return rx.toast("No slices selected for import.")
        all_slices = self.slices
        existing_slice_ids = {s.id for s in all_slices}
        imported_count = 0
        for new_slice in self.parsed_slices:
            if (
                new_slice.id in self.slices_to_import
                and new_slice.id not in existing_slice_ids
            ):
                all_slices.append(new_slice)
                existing_slice_ids.add(new_slice.id)
                imported_count += 1
        self.slices_json = json.dumps([s.model_dump() for s in all_slices])
        self.set_show_import_modal(False)
        return rx.toast(f"Successfully imported {imported_count} new slices.")

    @rx.event
    def delete_active_slice(self):
        if not self.active_slice_id or len(self.slices) <= 1:
            return rx.toast("Cannot delete the last slice.", duration=3000)
        all_slices = self.slices
        all_slices = [s for s in all_slices if s.id != self.active_slice_id]
        self.slices_json = json.dumps([s.model_dump() for s in all_slices])
        if all_slices:
            self.active_slice_id = all_slices[0].id
        else:
            self.create_new_slice()