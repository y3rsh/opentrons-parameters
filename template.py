import csv
from io import StringIO
from opentrons import protocol_api
from dataclasses import dataclass
from typing import List, Set, Union


metadata = {
    "name": "Template",
    "author": "Josh McVey",
    "description": "A template.",
}
requirements = {
    "robotType": "Flex",
    "apiLevel": "2.20",
}

TRASH_LOCATION = "A3"  # Where the trash is located
# We record the headers of the CSV file here so that we can validate that the CSV file we upload matches the expected format.
HEADERS = []


def add_parameters(parameters):
    parameters.add_str(
        display_name="Pipette Type & Tiprack",
        variable_name="pipette_and_tips",
        choices=[
            {
                "display_name": "50s w/ standard tips",
                "value": "flex_1channel_50,opentrons_flex_96_tiprack_50ul",
            },
            {
                "display_name": "50s w/ filter tips",
                "value": "flex_1channel_50,opentrons_flex_96_filtertiprack_50ul",
            },
            {
                "display_name": "1000s w/ standard 200 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_tiprack_200ul",
            },
            {
                "display_name": "1000s w/ filter 200 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_filtertiprack_200ul",
            },
            {
                "display_name": "1000s w/ standard 1000 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_tiprack_1000ul",
            },
            {
                "display_name": "1000s w/ filter 1000 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_filtertiprack_1000ul",
            },
        ],
        default="flex_1channel_50,opentrons_flex_96_tiprack_50ul",
        description="Select the pipette and tip type",
    )
    parameters.add_str(
        display_name="Pipette Mount",
        variable_name="pipette_mount",
        choices=[
            {"display_name": "left", "value": "left"},
            {"display_name": "right", "value": "right"},
        ],
        default="left",
        description="Select the pipette mount.",
    )
    parameters.add_csv_file(
        variable_name="my_csv",
        display_name="The CSV file",
        description="Template CSV file",
    )


def validate_data_rows(data_rows):
    """Process each row of data. Fail fast on the first row missing fields or that has empty fields"""
    for index, row in enumerate(data_rows, start=1):
        if len(row) != len(HEADERS):
            error = f"There are missing fields in data row: {index}, line {index+1} of the CSV. The row data is: {row}"
            raise ValueError(error)

        for value in row:
            if value is None or value.strip() == "":
                error = f"There are empty fields in data row: {index}, line {index+1} of the CSV. The row data is: {row}"
                raise ValueError(error)


@dataclass
class Transfer:
    """This class describes 1 row of CSV data.
    Using a dataclass allows us to use named attributes to access the data.
    """

    source_labware: str
    source_slot: str
    source_well: str
    source_height_above_bottom_mm: float
    destination_labware: str
    destination_slot: str
    destination_well: str
    volume_ul: float


@dataclass(frozen=True)
class LabwareSlot:
    """This class defines labware slots so that we can use python's set."
    This makes it easier to ensure we only load each labware once."""

    labware: str
    slot: str

    def __hash__(self):
        return hash((self.labware, self.slot))

    def __eq__(self, other):
        if not isinstance(other, LabwareSlot):
            return NotImplemented
        return (self.labware, self.slot) == (other.labware, other.slot)
