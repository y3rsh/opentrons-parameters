import csv
from io import StringIO
from opentrons import protocol_api
from dataclasses import dataclass
from typing import List, Set, Union
from opentrons.protocols.parameters.types import CSVParameter

metadata = {
    "name": "Cherrypicking Flex Every Run Parameters",
    "author": "Josh McVey",
    "description": "Original author Krishna Soma <krishna.soma@opentrons.com> \n CSV Template at https://docs.google.com/spreadsheets/d/14ctuhLQebPd7Q6TPAuprTjgQFuHeHKykg18x_xtMuW0/edit?usp=sharing",
}
requirements = {
    "robotType": "Flex",
    "apiLevel": "2.20",
}


def add_parameters(parameters):
    parameters.add_str(
        display_name="Pipette Type & Tiprack",
        variable_name="pipette_and_tips",
        choices=[
            {
                "display_name": "50 s w/ standard tips",
                "value": "flex_1channel_50,opentrons_flex_96_tiprack_50ul",
            },
            {
                "display_name": "50 s w/ filter tips",
                "value": "flex_1channel_50,opentrons_flex_96_filtertiprack_50ul",
            },
            {
                "display_name": "1000 s w/ standard 200 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_tiprack_200ul",
            },
            {
                "display_name": "1000 s w/ filter 200 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_filtertiprack_200ul",
            },
            {
                "display_name": "1000 s w/ standard 1000 tips",
                "value": "flex_1channel_1000,opentrons_flex_96_tiprack_1000ul",
            },
            {
                "display_name": "1000 s w/ filter 1000 tips",
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


@dataclass
class Transfer:
    source_labware: str
    source_slot: str
    _source_well: str
    source_height_above_bottom_mm: float
    destination_labware: str
    destination_slot: str
    _destination_well: str
    volume_ul: float

    @property
    def source_well(self):
        return self.format_well(self._source_well)

    @property
    def destination_well(self):
        return self.format_well(self._destination_well)

    @staticmethod
    def format_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))


@dataclass(frozen=True)
class LabwareSlot:
    labware: str
    slot: str

    def __hash__(self):
        return hash((self.labware, self.slot))

    def __eq__(self, other):
        if not isinstance(other, LabwareSlot):
            return NotImplemented
        return (self.labware, self.slot) == (other.labware, other.slot)


def read_transfers_from_list(
    data: List[List[Union[str, int, float]]]
) -> List[Transfer]:
    headers = data[0]
    transfers = []
    for row in data[1:]:
        row_dict = dict(zip(headers, row))
        transfer = Transfer(
            source_labware=str(row_dict["source_labware"]),
            source_slot=str(row_dict["source_slot"]),
            _source_well=str(row_dict["source_well"]),
            source_height_above_bottom_mm=float(
                row_dict["source_height_above_bottom_mm"]
            ),
            destination_labware=str(row_dict["destination_labware"]),
            destination_slot=str(row_dict["destination_slot"]),
            _destination_well=str(row_dict["destination_well"]),
            volume_ul=float(row_dict["volume_μl"]),
        )
        transfers.append(transfer)
    return transfers


def get_unique_labware_slots(transfers: List[Transfer]) -> Set[LabwareSlot]:
    unique_labware_slots = set()
    for transfer in transfers:
        unique_labware_slots.add(
            LabwareSlot(transfer.source_labware, transfer.source_slot)
        )
        unique_labware_slots.add(
            LabwareSlot(transfer.destination_labware, transfer.destination_slot)
        )
    return unique_labware_slots


FLEX_DECK_SLOTS = [
    "A1",
    "A2",
    "A3",
    "B1",
    "B2",
    "B3",
    "C1",
    "C2",
    "C3",
    "D1",
    "D2",
    "D3",
]


def run(ctx: protocol_api.ProtocolContext):

    # Get the values from the RTPs
    pipette_type = ctx.params.pipette_and_tips.split(",")[0]
    tip_type = ctx.params.pipette_and_tips.split(",")[1]
    pipette_mount = ctx.params.pipette_mount
    tip_reuse = ctx.params.tip_reuse
    cherrypicking_sequence = ctx.params.cherrypicking_sequence.parse_as_csv()

    # load trash
    TRASH_LOCATION = "A3"
    trash = ctx.load_trash_bin(TRASH_LOCATION)

    # read the transfer information from the csv
    transfers = read_transfers_from_list(cherrypicking_sequence)

    # load labware
    unique_labware_slots = get_unique_labware_slots(transfers)
    for labware_slot in unique_labware_slots:
        ctx.load_labware(labware_slot.labware, labware_slot.slot)

    # load tipracks
    tipracks = []

    for slot in FLEX_DECK_SLOTS:
        if not ctx.deck[slot] and slot != TRASH_LOCATION:
            tipracks.append(ctx.load_labware(tip_type, slot))

    # load pipette
    pipette = ctx.load_instrument(pipette_type, pipette_mount, tip_racks=tipracks)

    tip_count = 0
    tip_max = len(tipracks * 96)

    def pick_up():
        nonlocal tip_count
        if tip_count == tip_max:
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
