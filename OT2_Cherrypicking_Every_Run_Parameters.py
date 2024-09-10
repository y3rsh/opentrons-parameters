import csv
from io import StringIO
from opentrons import protocol_api
from dataclasses import dataclass
from typing import List, Set, Union

metadata = {
    "name": "Cherrypicking OT-2 Parameters",
    "author": "Josh McVey",
    "description": "Original author Krishna Soma <krishna.soma@opentrons.com> \n CSV Template at https://docs.google.com/spreadsheets/d/14ctuhLQebPd7Q6TPAuprTjgQFuHeHKykg18x_xtMuW0/edit?usp=sharing",
}
requirements = {
    "robotType": "OT-2",
    "apiLevel": "2.20",
}

# We record the headers of the CSV file here so that we can validate that the CSV file we upload matches the expected format.
HEADERS = [
    "source_labware",
    "source_slot",
    "source_well",
    "source_height_above_bottom_mm",
    "destination_labware",
    "destination_slot",
    "destination_well",
    "volume_μl",
]


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


def read_transfers_from_list(
    data: List[List[Union[str, int, float]]],
) -> List[Transfer]:
    """This function reads a list of lists and returns a list of Transfer objects"""

    # the first row of our data is the headers
    headers = data[0]
    assert headers == HEADERS, f"Expected headers: {HEADERS}, but got: {headers}"
    # ignore the first row, as it is the headers
    data_rows = data[1:]
    validate_data_rows(data_rows)
    # Iterate over the rest of the rows and create Transfer objects
    # We will iterate over to take action in the protocol.
    transfers = []

    for row in data[1:]:
        # CSV data is inherently ordered so we can use the index to access the correct value
        # Processing the row data into a Transfer object allows us to use named attributes to access the data
        transfer = Transfer(
            source_labware=str(row[0]),
            source_slot=str(row[1]),
            source_well=str(row[2]),
            source_height_above_bottom_mm=float(row[3]),
            destination_labware=str(row[4]),
            destination_slot=str(row[5]),
            destination_well=str(row[6]),
            volume_ul=float(row[7]),
        )
        transfers.append(transfer)
    return transfers


def get_unique_labware_slots(transfers: List[Transfer]) -> Set[LabwareSlot]:
    """This function takes a list of Transfer objects and returns a set of unique LabwareSlot objects.
    The purpose of this function is to ensure that we only load each labware once."""
    unique_labware_slots = set()
    for transfer in transfers:
        unique_labware_slots.add(
            LabwareSlot(transfer.source_labware, transfer.source_slot)
        )
        unique_labware_slots.add(
            LabwareSlot(transfer.destination_labware, transfer.destination_slot)
        )
    return unique_labware_slots


def add_parameters(parameters):
    parameters.add_str(
        display_name="Pipette Mount",
        variable_name="pipette_mount",
        choices=[
            {"display_name": "left", "value": "left"},
            {"display_name": "right", "value": "right"},
        ],
        default="right",
        description="Select the pipette mount.",
    )
    parameters.add_str(
        display_name="Tip Reuse",
        variable_name="tip_reuse",
        choices=[
            {"display_name": "never", "value": "never"},
            {"display_name": "always", "value": "always"},
        ],
        default="always",
        description="Select the tip reuse.",
    )
    parameters.add_csv_file(
        variable_name="cherrypicking_sequence",
        display_name="Cherrypicking Sequence",
        description="Table of labware, wells, and volumes to transfer.",
    )


OT2_DECK_LOCATIONS = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
]


def print_output_of_parse_as_csv(data, ctx):
    for index, row in enumerate(data):
        ctx.comment(f"Row {index}:")
        ctx.comment(f"{', '.join([item for item in row])}")


def run(ctx: protocol_api.ProtocolContext):

    # Get the values from the RTPs
    pipette_mount = ctx.params.pipette_mount
    tip_reuse = ctx.params.tip_reuse
    cherrypicking_sequence = ctx.params.cherrypicking_sequence.parse_as_csv()
    print_output_of_parse_as_csv(cherrypicking_sequence, ctx)
    # read the transfer information from the csv
    transfers = read_transfers_from_list(cherrypicking_sequence)

    # load labware
    unique_labware_slots = get_unique_labware_slots(transfers)
    for labware_slot in unique_labware_slots:
        ctx.load_labware(labware_slot.labware, labware_slot.slot)

    # load tipracks
    tipracks = []

    for slot in OT2_DECK_LOCATIONS:
        if not ctx.deck[slot]:
            tipracks.append(ctx.load_labware("opentrons_96_tiprack_300ul", slot))

    # load pipette
    pipette = ctx.load_instrument("p300_single_gen2", pipette_mount, tip_racks=tipracks)

    tip_count = 0
    tip_max = len(tipracks) * 96

    def pick_up():
        nonlocal tip_count
        if tip_count >= tip_max:
            ctx.pause("Please refill tipracks before resuming.")
            pipette.reset_tipracks()
            tip_count = 0
        pipette.pick_up_tip()
        tip_count += 1

    if tip_reuse == "never":
        pick_up()

    for transfer in transfers:
        source = (
            ctx.deck[transfer.source_slot]
            .wells_by_name()[transfer.source_well]
            .bottom(transfer.source_height_above_bottom_mm)
        )
        destination = ctx.deck[transfer.destination_slot].wells_by_name()[
            transfer.destination_well
        ]
        if tip_reuse == "always":
            pick_up()
        pipette.transfer(
            float(transfer.volume_ul), source, destination, new_tip="never"
        )
        if tip_reuse == "always":
            pipette.drop_tip()
    if pipette.has_tip:
        pipette.drop_tip()
