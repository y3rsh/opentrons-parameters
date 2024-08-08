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
            LabwareSlot(labware=transfer.source_labware, slot=transfer.source_slot)
        )
        unique_labware_slots.add(
            LabwareSlot(
                labware=transfer.destination_labware, slot=transfer.destination_slot
            )
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


def run(ctx: protocol_api.ProtocolContext):

    # Get the values from the RTPs
    pipette_mount = ctx.params.pipette_mount
    tip_reuse = ctx.params.tip_reuse
    cherrypicking_sequence = ctx.params.cherrypicking_sequence.parse_as_csv()

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
